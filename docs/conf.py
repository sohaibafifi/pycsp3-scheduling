# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path for autodoc
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pycsp3-scheduling"
copyright = "2026, Sohaib AFIFI"
author = "Sohaib AFIFI"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Support for Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.intersphinx",  # Link to other projects' documentation
    "sphinx.ext.autosummary",  # Generate summary tables
    "sphinx.ext.mathjax",  # Render math in notebooks/Markdown
    "myst_nb",  # Support for Markdown and Jupyter notebooks
    "sphinx_copybutton",  # Copy button for code blocks
]

# MyST-NB settings
nb_execution_mode = "off"  # Don't execute notebooks during build
nb_render_image_options = {"align": "center"}
myst_enable_extensions = [
    "amsmath",
    "dollarmath",
]

# Napoleon settings for docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# Autosummary settings
autosummary_generate = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Source file extensions - myst_nb handles both .md and .ipynb
source_suffix = {
    ".rst": "restructuredtext",
    ".ipynb": "myst-nb",
    ".md": "myst-nb",
}

# The master toctree document
master_doc = "index"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Furo theme options - elegant and minimal
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
        "font-stack": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font-stack--monospace": "'JetBrains Mono', 'Fira Code', monospace",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#60a5fa",
    },
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "top_of_page_button": "edit",
}

# Additional HTML settings
html_title = "PyCSP<sup>3</sup>-Scheduling"
html_short_title = "PyCSP3-Scheduling"
html_show_sourcelink = False
html_copy_source = False

# -- Options for autodoc -----------------------------------------------------

# Mock imports for modules that may not be available during doc building
autodoc_mock_imports = ["pycsp3", "lxml"]

# -- Custom setup ------------------------------------------------------------


def setup(app):
    """Custom Sphinx setup."""
    # Create _static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), "_static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
