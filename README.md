# Python installation

1.  Create Python environment

    ```python
        python -m venv env
    ```

    ```python3
        python3 -m venv env
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

4.  Run virtual environment

    ```python
        uvicorn main:app
    ```
