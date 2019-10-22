#!/bin/bash

isort -rc hmt_cite_atlas
black hmt_cite_atlas
flake8 hmt_cite_atlas
