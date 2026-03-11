# Mills Art Museum Project: Generating AAT Keywords for the Museum Collection


# Goal

Labeling Art Museum pieces has previously been a tedious and time-consuming task at the Mills College Art Museum. 
In light of recent advancements in image recognition and object categorization, the goal of this project is to lay the stones,
for potential future applications of modern AI and ML techniques to the general art community. 


# Background & Why

At Mills College, museum staff each assign each art piece a keyword that best represent the piece's content, from a 
total collection of 50,000 keywords. This has slowed down the labeling process and has resulted in a large number of 
pieces not being labeled, and highlighted the need for a more streamlined & automated process.


# How?

This project can be devided into two parts:
1. A central user interface to generate AAT keywords for the entire collection of art pieces
2. A pipeline to handle unique AAT datasets, their respective refinement, cleaning, and finally matching process for each museum piece.


## User Interface
The user interface is the connector between what museum staff interact and the art peice labeling pipeline. It allows 
for a clean centralized interface for uploading, monitoring, and extracting images with their respective AAT keywords. 
It allows the user to approve or reject keyword recommendations and allows for user-to-agent communication to
improve the quality of the labeling process.

### Specs

[!IMPORTANT]
Hi team, finish the UI design specifications as well as a brief general design choice.


## Pipeline
The pipeline is the core of the project; it encompasses the entire process of filtering, cleaning, and matching 
AAT keywords to art pieces. This allows user the staff to have a streamlined process, from separate museum collections and
ATT keyword dataset.

### Specs

Our pipeline is implemented in the Python programming language, due to the familiarity of the team with the language as well as the prominence of machine learning libraries and wrappers for the language. Powerful libraries such as pytorch make Python a premiere choice for machine learning work across the industry.

For our machine learning models, we chose Qwen3VL Embedder and Reranker models. These models have the benefit of being open-weight, which allows us to easily make any necessary adjustments easily, as well as being (close to) State of The Art in this space. Qwen as a whole is a rising force in the AI model space, with their propensity to release a wide range of variants and sizes for their models (as well as the previously mentioned open weights) making them particularly popular among local hosting and finetuning circles. The Embedder model generates embeddings based on the image, associating them with specific concepts; in our case, we fit the embedding model onto a filtered version of the AAT terms so that the embeddings it would generate are AAT terms. The Reranker model takes the embeddings generated and re-ranks them, which allows us to further refine the output and increase the quality of results.

The pipeline is primarily designed around using Google Colab, as their rather generous educational benefits package has given us access to far more powerful hardware than we would otherwise have access too, and in general the platform allows for workflows to be very easily shared and used. We also believe that Colab's pay-as-you-go style of pricing will be very attractive to small museums, as it means that they only pay for what they use and they don't need to worry about the various costs of maintaining infrastructure or hardware themselves.
