
# Vault Test

The intent of this project was to familiarize myself with Hashicorps Vault, and
how it's appauth mechanism can be used for a custom service, refered to in this
context as "app". This project had several goals:

- Minimise password/token use outside the app

    We want to reduce the possible attack surface with regard to secrets. All
    application related secrets should be stored within vault. We only want to
    store temporary secrets if possible. It's common to store secrets in
    environment variables and secured config files, but these have various short
    comings, so we'd like to minimise the use of these methods.
- Minimise custom scripting needed at the CI/CD layer

    There is no formal CI/CD system built into this project (docker-compose
    doesn't count in this case). The CD system would be responsible for rendering
    the application config file, which is were the temporary auth token is
    generated. Since the token is valid for only about 1 minute, a token would
    need to be generated each time the container starts up. How containers are
    started may vary significantly depending on infrastructure, so we shouldn't
    assume we can run much logic before starting the container.
- Make it easy to add more passwords to app in the future

    For instance, I might want to implement caching with redis at a later date,
    which would require another set of credentials. I should be able to add that
    password without having to make major changes to the configuration system
    (both in source code, and in code infrastructure)

## Setup

Required utilities:

- docker
- docker-compose
- pip
- jq
- mustache
- vault

### Database

Before testing the application and pulling secrets from vault, we need to set up
the database, whose password we'll be storing in vault, as well as the vault
server itself.

Bring the database up, apply the migrations and verify you can connect with the
account set in the docker compose file.

```
$ docker-compose up -d db
$ PGPASSWORD=acKQfbU9PmKKsWu9 psql -U app-user -h localhost app-db < sql/schema.sql
$ PGPASSWORD=acKQfbU9PmKKsWu9 psql -U app-user -h localhost app-db < sql/data.sql
```

### Vault

Start the server and grab the root key for initial setup. Once started, you can
log into the web interface at `http://localhost:8200` with the root token.

```
$ docker-compose up -d vault
$ export VAULT_TOKEN=$(docker-compose logs vault | grep 'Root Token:' | awk '{print $NF}')
$ echo $VAULT_TOKEN
s.29aVhedp1lhasRKB5bmoNWXS
```

Create a key-value secret to store app passwords in, create a policy allowing
read access to the new secret.

```
$ export VAULT_ADDR=http://localhost:8200/
$ vault kv put secret/app database_password=acKQfbU9PmKKsWu9
$ vault policy write app vault/app.hcl
```

Enable approle authentication, create a new role for our application (configured
with short token lifespans), and create a policy for generating login tokens for
the new role.

```
$ vault auth enable approle
$ vault write auth/approle/role/app secret_id_ttl=1m token_ttl=1m token_max_tll=1m policies="app"
$ vault write sys/policy/ar-token-create policy=@vault/ar-token-create.hcl
```

### Application startup

Build the image for the app:

```
$ docker-compose build app
```

The approle authentication is handled within the `render-auth.sh` script, which
gets the role_id for the "app" role, then gets a new token for the role (requires
having the `VAULT_TOKEN` environment variable set). A json object is manually
built with these two values, and passed to `mustache`, which templates them into
the `app/settings.yml.mustache` file. This script creates the `app/settings.yml`
file.

Once the app settings file is rendered, we can start the app container.

```
$ ./render-auth.sh
$ docker-compose up app
```

The api for the app is at `http://localhost:8000`, which in this case is really
only useful for confirming the whole stack is working.
