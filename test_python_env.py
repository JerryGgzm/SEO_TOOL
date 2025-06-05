# 在Python环境中运行以下代码验证关键包是否正确安装
import fastapi
import flask
import sqlalchemy
import pandas
import numpy
import spacy
import nltk
import pytest

print(f"FastAPI version: {fastapi.__version__}")
print(f"Flask version: {flask.__version__}")
print(f"SQLAlchemy version: {sqlalchemy.__version__}")
print(f"Pandas version: {pandas.__version__}")
print(f"NumPy version: {numpy.__version__}")
print(f"Spacy version: {spacy.__version__}")
print(f"NLTK version: {nltk.__version__}")
print(f"Pytest version: {pytest.__version__}")