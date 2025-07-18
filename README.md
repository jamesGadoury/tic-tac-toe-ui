# tic tac toe

### run tests:

```
# start server
python -m http.server 8000
```

open this in your browser: http://localhost:8000/tests/test.html


### install typescript

install nvm first:

```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# Restart shell, then install node:
nvm install node
```
then install typescript:

```

npm install -g typescript
```

You also might have to set the default npm for nvm to use in your .zshrc (or .bashrc):

```
# in shell you installed nvm:
nvm alias default node

# then add to relevant .zshrc or .bashrc file the version, e.g.
nvm alias default 24.4.1
```

