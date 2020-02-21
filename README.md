# Python installation

1. Create Python environment

   ```python
       python3 -m venv env
   ```

2. Activate environment

   ```python
       source env/bin/activate
   ```

3. Install pydfs-lineup-optimizer

   ```python
       pip3 install pydfs-lineup-optimizer
   ```

## Run flask app

```python
    export FLASK_APP=app.py
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
