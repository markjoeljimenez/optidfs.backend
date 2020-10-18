# Python installation

1.  Create Python environment

    ```python
        python3 -m venv env

        (Windows)
        python -m venv env
    ```

2.  Activate environment

    ```python
        source env/bin/activate

        (Windows)
        ./env/Scripts/activate
    ```

3.  Install requirements

    ```python
        pip install -r requirements.txt
    ```

4.  Set Flask and run virtual environment

        ```python
            set FLASK_APP=application.py
            flask run
        ```
