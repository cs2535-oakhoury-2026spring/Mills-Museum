# Image Pipeline Dependencies
Our image pipeline relies upon a variety of packages outside of the Python Standard Library. Many of these dependencies are directly involved in the running of our AI models, whereas others are helpers for more tertiary tasks. These dependencies are contained in the [requirements.txt](/requirements.txt) for easy installation using `pip install -r requirements.txt`. For your convenience, we also list them out below, alongside links to the packages in question and any explanations for why we chose those particular packages.

## Pip Dependencies Used and Our Reasoning
- [torch](https://pypi.org/project/torch/): **The** library for machine learning in Python, used very widely throughout the ecosystem. It allows us to easily run AI models without getting into the minutiae of how to do so.
- [transformers](https://pypi.org/project/transformers/): A library that allows programmers to easily fetch and use models from HuggingFace. This is a dependency of the model-specific packages we also use.
- [chromadb](https://pypi.org/project/chromadb/): Chromadb is one of the most popular libraries for databases in AI and Machine Learning applications, and is particularly notable for handling the storage and searching of **Vectors**, which are an incredibly important part of our pipeline (as we generate a vector for each image, and search our chromadb database of AAT terms to find the terms that are most similar).
- [datasets](https://pypi.org/project/datasets/): In short, this is the equivalent of `transformers` but for datasets instead of models. It allows for easily pulling from datasets on HuggingFace, and is particularly important for us when embedding the AAT terms into the vector database.
- [qwen-vl-utils](https://pypi.org/project/qwen-vl-utils/): These are an official set of helper scripts for working with Qwen's Visual Language models. As such, we use this to help run our Embedding and Reranking models.
- [hf_xet](https://pypi.org/project/hf-xet/): This is a minor library that we don't use directly, but instead simply improves the efficiency of data transfer to and from HuggingFace. We use it primarily to speed up the fetching of the models.
- [langchain-chroma](https://pypi.org/project/langchain-chroma/): LangChain's integration with ChromaDB. We primarily use it for the feature of being able to do a more advanced query on the vector database using MMR (Maximal Marginal Relevance), which helps us to increase the variety among our keywords generated for each image.
- [langchain-core](https://pypi.org/project/langchain-core/): The core of LangChain, needed for `langchain-chroma`.
- [Pillow](https://pypi.org/project/Pillow/): A fork of the now-abandoned Python Imaging Library, it allows us to work with images more programmatically rather than always passing around file paths.
- [gradio](https://pypi.org/project/gradio/): One of the most common frameworks for WebUI in Python for the Machine Learning community. We use it primarily for the data visualization UI, and in the past it was the basis of our demo versions of the main image pipeline UI before we switched to using React and Vite.
- [huggingface_hub](https://pypi.org/project/huggingface_hub/): The main huggingface library for general downloads; the main consumer of `hf_xet`.
- [accelerate](https://pypi.org/project/accelerate/): A library that helps abstract away interacting with multiple different types of device for machine learning, which otherwise can be quite a lot of boilerplate.
- [pandas](https://pypi.org/project/pandas/): Just as much of a gold standard in Machine Learning as it is in data science.
- [pyarrow](https://pypi.org/project/pyarrow/): Used by the data visualization UI, provides a Python API for the Arrow C++ library.
- [plotly](https://pypi.org/project/plotly/): Used by the data visualization UI, acts as a browser-based graphing library.
- [tqdm](https://pypi.org/project/tqdm/): Prettier progress bars for any iterables in the colab.

## Non-Pip Dependencies
A couple of our dependencies are not found in Pip, primarily due to us wanting the ability to potentially make changes to them if need be. In particular:
- `qwen3_vl_embedding`: A helper script specific to the Qwen 3 VL Embedding model that we use, handling a lot of the tedious boilerplate of formatting the inputs correctly for running the model.
- `qwen3_vl_reranker`: The same as the former, but for the reranker model instead of the embedding model.