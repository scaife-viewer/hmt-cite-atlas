#!/bin/bash

isort -rc hmt_cite_atlas
black --exclude "/migrations/" hmt_cite_atlas
flake8 hmt_cite_atlas
