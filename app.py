import warnings
from pathlib import Path

import duckdb
import joblib
#import mols2grid
import numpy as np
import pandas as pd
import streamlit as st
import useful_rdkit_utils as uru
from lightgbm import LGBMRegressor
from rdkit import Chem
from rdkit.Chem import Draw
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split


DATA_PATH = Path("data/raw/bindingdb_sample.ddb")
MODEL_PATH = Path("models/pxr_lgbm_model.joblib")
UNIPROT_ID = "O75469"


st.set_page_config(
    page_title="BindingDB QSAR Studio",
    page_icon="🧪",
    layout="wide",
)


@st.cache_data
def load_pxr_data(uniprot_id: str = UNIPROT_ID) -> pd.DataFrame:
    """Load PXR assay data from the local BindingDB DuckDB sample database."""
    if not DATA_PATH.exists():
        st.error(f"BindingDB sample database not found at: {DATA_PATH}")
        st.stop()

    query = f"""
        SELECT
            "Ligand SMILES",
            "Ligand InChI Key",
            "BindingDB Ligand Name",
            "Target Name",
            "Target Source Organism According to Curator or DataSource",
            "Article DOI",
            "PDB ID(s) for Ligand-Target Complex",
            "EC50 (nM)"
        FROM bindingdb
        WHERE "UniProt (SwissProt) Primary ID of Target Chain 1" = '{uniprot_id}'
    """

    with duckdb.connect(str(DATA_PATH)) as con:
        df = con.execute(query).df()

    return df


def clean_ec50_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean EC50 values and convert EC50 nM to pEC50."""
    clean_df = df.copy()

    clean_df = clean_df.dropna(subset=["EC50 (nM)"])
    clean_df["EC50 (nM)"] = clean_df["EC50 (nM)"].astype(str)

    clean_df["has_operator"] = clean_df["EC50 (nM)"].str.contains("<|>", regex=True)
    clean_df["EC50_numeric"] = (
        clean_df["EC50 (nM)"]
        .str.replace("<", "", regex=False)
        .str.replace(">", "", regex=False)
        .astype(float)
    )

    clean_df["pEC50"] = -np.log10(clean_df["EC50_numeric"] * 1e-9)

    return clean_df


def aggregate_by_ligand(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate replicate measurements to one mean pEC50 per ligand."""
    df_no_operators = df.query("has_operator == False").copy()

    agg_list = []

    for inchi_key, group in df_no_operators.groupby("Ligand InChI Key"):
        smiles = group["Ligand SMILES"].iloc[0]
        mean_pec50 = group["pEC50"].mean()
        agg_list.append(
            {
                "Ligand InChI Key": inchi_key,
                "SMILES": smiles,
                "pEC50": mean_pec50,
                "measurement_count": len(group),
            }
        )

    return pd.DataFrame(agg_list)


@st.cache_data
def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate RDKit descriptors for each molecule."""
    rdkit_desc = uru.RDKitDescriptors()
    desc_df = df.copy()
    desc_df["desc"] = desc_df["SMILES"].apply(rdkit_desc.calc_smiles)
    desc_df = desc_df.dropna(subset=["desc"])

    return desc_df


def train_model(df: pd.DataFrame, test_size: float, random_state: int):
    """Train a LightGBM model using RDKit descriptors."""
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
    )

    model = LGBMRegressor(verbose=-1)

    x_train = np.stack(train_df["desc"])
    y_train = train_df["pEC50"]

    x_test = np.stack(test_df["desc"])
    y_test = test_df["pEC50"]

    model.fit(x_train, y_train)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        predictions = model.predict(x_test)

    r2 = r2_score(y_test, predictions)

    return model, train_df, test_df, predictions, r2


def predict_smiles(smiles: str, model) -> float:
    """Predict pEC50 for a user-entered SMILES."""
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        raise ValueError("Invalid SMILES string.")

    rdkit_desc = uru.RDKitDescriptors()
    desc = rdkit_desc.calc_smiles(smiles)

    prediction = model.predict(np.array(desc).reshape(1, -1))[0]

    return float(prediction)


def render_molecule(smiles: str):
    """Render molecule image from SMILES."""
    mol = Chem.MolFromSmiles(smiles)

    if mol is None:
        return None

    return Draw.MolToImage(mol)


st.title("BindingDB QSAR Studio")
st.caption(
    "A first Streamlit application converting the Practical Cheminformatics "
    "BindingDB PXR notebook into an interactive scientific ML workflow."
)

tab_data, tab_train, tab_predict = st.tabs(
    ["1. Data", "2. Train Model", "3. Predict"]
)


with tab_data:
    st.header("BindingDB Target Data")

    st.markdown(
        """
        Version 0.1 uses the original notebook target: **Pregnane X Receptor (PXR)**.

        - UniProt ID: `O75469`
        - Activity endpoint: `EC50`
        - Data source: local BindingDB DuckDB sample
        """
    )

    raw_df = load_pxr_data()
    clean_df = clean_ec50_data(raw_df)
    agg_df = aggregate_by_ligand(clean_df)

    col1, col2, col3 = st.columns(3)

    col1.metric("Raw records", len(raw_df))
    col2.metric("Clean EC50 records", len(clean_df))
    col3.metric("Unique ligands", len(agg_df))

    st.subheader("Cleaned Data Preview")
    st.dataframe(
        clean_df[
            [
                "Ligand SMILES",
                "Ligand InChI Key",
                "Target Name",
                "Article DOI",
                "EC50 (nM)",
                "pEC50",
                "has_operator",
            ]
        ].head(100),
        use_container_width=True,
    )

    st.subheader("pEC50 Distribution")
    st.bar_chart(clean_df["pEC50"].value_counts(bins=20).sort_index())


with tab_train:
    st.header("Train LightGBM QSAR Model")

    st.markdown(
        """
        This tab aggregates ligand measurements, calculates RDKit descriptors,
        trains a LightGBM regression model, and saves the trained model artifact.
        """
    )

    test_size = st.slider("Test set fraction", 0.1, 0.5, 0.2, 0.05)
    random_state = st.number_input("Random seed", value=42, step=1)

    if st.button("Train Model"):
        raw_df = load_pxr_data()
        clean_df = clean_ec50_data(raw_df)
        agg_df = aggregate_by_ligand(clean_df)

        with st.spinner("Calculating RDKit descriptors..."):
            model_df = calculate_descriptors(agg_df)

        with st.spinner("Training LightGBM model..."):
            model, train_df, test_df, predictions, r2 = train_model(
                model_df,
                test_size=test_size,
                random_state=int(random_state),
            )

        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": model,
                "training_data": model_df,
                "test_size": test_size,
                "random_state": int(random_state),
                "r2": r2,
            },
            MODEL_PATH,
        )

        st.success(f"Model trained and saved to `{MODEL_PATH}`")

        col1, col2, col3 = st.columns(3)
        col1.metric("Training molecules", len(train_df))
        col2.metric("Test molecules", len(test_df))
        col3.metric("R²", f"{r2:.3f}")

        result_df = pd.DataFrame(
            {
                "Observed pEC50": test_df["pEC50"].values,
                "Predicted pEC50": predictions,
                "SMILES": test_df["SMILES"].values,
            }
        )

        st.subheader("Prediction Results")
        st.dataframe(result_df, use_container_width=True)

        st.subheader("Observed vs Predicted pEC50")
        st.scatter_chart(
            result_df,
            x="Observed pEC50",
            y="Predicted pEC50",
        )


with tab_predict:
    st.header("Predict Activity from SMILES")

    st.markdown(
        """
        Enter a molecule as a SMILES string and use the saved model to predict
        PXR activity as pEC50.
        """
    )

    if not MODEL_PATH.exists():
        st.warning("No trained model found yet. Train a model in the previous tab first.")
    else:
        model_bundle = joblib.load(MODEL_PATH)
        model = model_bundle["model"]

        smiles = st.text_input(
            "SMILES",
            value="CC(C)(C)OC(=O)N1CCC(CC1)N2CCN(CC2)C3=NC=CC=N3",
        )

        if smiles:
            mol_img = render_molecule(smiles)

            if mol_img is None:
                st.error("Invalid SMILES string.")
            else:
                st.image(mol_img, caption="Input molecule", width=300)

                if st.button("Predict pEC50"):
                    try:
                        prediction = predict_smiles(smiles, model)

                        st.success("Prediction complete")
                        st.metric("Predicted pEC50", f"{prediction:.2f}")

                        ec50_nm = 10 ** (-prediction) * 1e9
                        st.metric("Approximate EC50", f"{ec50_nm:.2f} nM")

                    except Exception as exc:
                        st.error(f"Prediction failed: {exc}")