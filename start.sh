#!/bin/bash
gunicorn keep_alive:app & python main.py
