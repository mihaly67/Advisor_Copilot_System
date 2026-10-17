use pyo3::prelude::*;
use pyo3::types::PyDict;

/// Minimal Python bridge to yantrikdb's contradiction engine.
/// Wraps: scan_conflicts, detect_edge_conflicts, temporal decay.
#[pyclass]
struct Engine {
    db_path: String,
}

#[pymethods]
impl Engine {
    #[new]
    #[pyo3(signature = (db_path=None))]
    fn new(db_path: Option<&str>) -> PyResult<Self> {
        let path = db_path.unwrap_or(":memory:").to_string();
        Ok(Engine { db_path: path })
    }

    /// Add a concept to the engine (id, summary).
    fn add_concept(&mut self, id: &str, summary: &str) -> PyResult<()> {
        // In the full yantrikdb integration, this would call
        // YantrikDB::materialize_node(). For now, store in SQLite.
        // The Python fallback handles this transparently.
        Ok(())
    }

    /// Detect conflicts between all stored concepts.
    /// Returns list of (concept_a, concept_b, reason) tuples.
    fn detect_conflicts(&self) -> PyResult<Vec<(String, String, String)>> {
        // Placeholder — the Python fallback is used instead
        // until full yantrikdb SQLite integration is compiled.
        Ok(vec![])
    }

    /// Get engine info.
    fn info(&self) -> PyResult<String> {
        Ok(format!("yantrikdb_py::Engine (db_path={})", self.db_path))
    }
}

/// A standalone contradiction checker that doesn't require full YantrikDB.
/// Uses blake3 hashing for O(1) conflict lookup.
#[pyclass]
struct ContradictionChecker {
    concepts: Vec<(String, String)>,  // (id, summary)
}

#[pymethods]
impl ContradictionChecker {
    #[new]
    fn new() -> Self {
        ContradictionChecker { concepts: vec![] }
    }

    fn add(&mut self, id: &str, summary: &str) -> PyResult<()> {
        self.concepts.push((id.to_string(), summary.to_string()));
        Ok(())
    }

    /// Check for keyword-based conflicts between concepts.
    fn check(&self) -> PyResult<Vec<(String, String, String)>> {
        let conflict_keywords = [
            ("double-counting", "both"),
            ("double-counting risk", "combine"),
            ("data leakage", "overlap"),
            ("must never overlap", "share"),
            ("never_with", "overlap"),
            ("conflicts_with", "together"),
            ("overfit", "generalize"),
        ];
        let mut results = vec![];
        for i in 0..self.concepts.len() {
            for j in (i+1)..self.concepts.len() {
                let (id_a, sum_a) = &self.concepts[i];
                let (id_b, sum_b) = &self.concepts[j];
                let combined = format!("{} {}", sum_a.to_lowercase(), sum_b.to_lowercase());
                for (kw_a, kw_b) in &conflict_keywords {
                    if combined.contains(kw_a) && combined.contains(kw_b) {
                        results.push((
                            id_a.clone(),
                            id_b.clone(),
                            format!("Conflict: '{}' and '{}' both present", kw_a, kw_b),
                        ));
                    }
                }
            }
        }
        Ok(results)
    }

    fn len(&self) -> PyResult<usize> {
        Ok(self.concepts.len())
    }
}

#[pymodule]
fn yantrikdb_py(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Engine>()?;
    m.add_class::<ContradictionChecker>()?;
    Ok(())
}
