[![Build Status](https://img.shields.io/circleci/build/bb/metalgear121/pac-client?token=3dee960889ae341ab0a6b5a333b481d1f0426866)](https://circleci.com/bb/metalgear121/pac-server)
[![Python Version](https://img.shields.io/badge/Python-v3.7.5-blue)](https://www.python.org)
[![Django Version](https://img.shields.io/badge/Django-v3.1.2-blue)](https://www.djangoproject.com)

# GUI Service
A web service for public dating in Japan

## Overview

- Order register, matching
- Search casts and guests
- Group chat and private chat
- Tweet of users
- Notification and profile

## Main Features

- DRF RestfulAPI (function, class-based, generic views) 
- SimpleUI for django admin
- Django channels and celery with redis
- Django cronjob using celery
- Swagger API Documentation
- AWS deployment

## Getting Started

First clone the repository from Github and switch to the new directory:

    $ git clone git@github.com/david1992121/gui-engine.git
    
Activate the virtualenv for your project.
    
Install project dependencies:

    $ pip install -r requirements.txt
    
    
Then simply apply the migrations:

    $ python manage.py migrate
    

You can now run the development server:

    $ python manage.py runserver