# database.py
from flask import Flask, current_app, request, abort
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
