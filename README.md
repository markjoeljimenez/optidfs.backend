# Python installation

1. Create Python environment

    ```python
        python3 -m venv env

        (Windows)
        python -m venv env
    ```

2. Activate environment

    ```python
        source env/bin/activate

        (Windows)
        ./env/Scripts/activate
    ```

3. Install requirements

    ```python
        pip install -r requirements.txt
    ```

4. Set Flask and run virtual environment

    ```python
        set FLASK_APP=app.py
        flask run
    ```

## Deploy to Heroku

1. Login to Heroku using CLI

   ```cli
       heroku login
   ```

2. Clone repo to Heroku

   ```cli
       heroku git:clone -a evening-brushlands-00691
       cd evening-brushlands-00691
   ```

3. Deploy

   ```cli
       git add .
       git commit -am "{COMMIT}"
       git push heroku master
   ```

## Clear Heroku cache

```cli
    heroku plugins:install heroku-repo
    heroku repo:purge_cache -a evening-brushlands-00691
    git commit --allow-empty -m "Purge cache"
    git push heroku master
```
