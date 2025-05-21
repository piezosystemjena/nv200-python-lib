Installation
================

Quick Install
^^^^^^^^^^^^^^^^

If you're already familiar with Python and just want to install the package quickly then:

.. code-block:: bash

    pip install nv200

or if you would like to install the package into a virtual environment:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    pip install nv200


Step-by-Step Installation Guide
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This guide provides instructions for installing the `nv200` package.

Prerequisites
""""""""""""""""""""""""

Before installing the package, make sure that:

- You have Python installed (version > 3.12 is required).
- You have `pip` installed, which is the package installer for Python.
- You have `virtualenv` installed, which can be used to create isolated Python environments.



Step 1 - Install virtualenv (if not already installed)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

If you don't have `virtualenv` installed, you can install it by running the following command:

.. code-block:: cmd

    pip install virtualenv


Step 2 - Create a Virtual Environment
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

To create a new virtual environment, navigate to the directory where you want the environment to be created. 
Then, run the following command:

.. code-block:: cmd

    virtualenv .venv

This will create a virtual environment named :file:`.venv` in the current directory. You can choose a 
different name for the environment if needed.


Step 3 - Activate the Virtual Environment
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Once the virtual environment is created, you need to activate it. The activation command depends 
on your operating system.

.. code-block:: cmd

    .venv\Scripts\activate


Step 4 - Install the Wheel
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

With the virtual environment activated, you can now install the NV200 package.

.. code-block:: cmd

    pip install nv200


Summary
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

So to install the NV200 package into a virtual environment, you execute the following commands:


.. code-block:: bash

    virtualenv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    pip install nv200

