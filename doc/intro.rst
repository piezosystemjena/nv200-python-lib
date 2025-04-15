Introduction
==================================

This library provides an Python interface for controlling and communicating with the 
NV200 device from `piezosystem Jena <https://www.piezosystem.com>`_.

Installation
================

This guide provides instructions for installing the `nv200_python_lib` package locally from a :file:`.whl` 
(wheel) file within a Python virtual environment.

Prerequisites
^^^^^^^^^^^^^^^^

Before installing the package, make sure that:

- You have Python installed (version 3.x is required).
- You have `pip` installed, which is the package installer for Python.
- You have `virtualenv` installed, which can be used to create isolated Python environments.

Step 1: Install virtualenv (if not already installed)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you don't have `virtualenv` installed, you can install it by running the following command:

.. code-block:: cmd

    pip install virtualenv


Step 2: Create a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a new virtual environment, navigate to the directory where you want the environment to be created. 
Then, run the following command:

.. code-block:: cmd

    virtualenv .venv

This will create a virtual environment named :file:`.venv` in the current directory. You can choose a 
different name for the environment if needed.


Step 3: Activate the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the virtual environment is created, you need to activate it. The activation command depends 
on your operating system.

.. code-block:: cmd

    .venv\Scripts\activate


Step 4: Install the Wheel File with pip
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the virtual environment activated, you can now install the :file:`.whl` file 
using `pip`. 

.. code-block:: cmd

    pip install nv200-py3-none-any.whl


.. rst-class:: steps
