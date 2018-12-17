
# Vault Test

Required utilities:

- docker
- docker-compose
- pip
- jq
- mustache
- vault

## Initial setup

Before testing the application and pulling secrets from vault, we need to set up
the database, whose password we'll be storing in vault, as well as the vault
server itself.

### Database

Bring the database up, apply the migrations and verify you can connect with the
account set in the docker compose file.

```
$ docker-compose up -d db
$ PGPASSWORD=acKQfbU9PmKKsWu9 psql -U app-user -h localhost app-db < sql/schema.sql
$ PGPASSWORD=acKQfbU9PmKKsWu9 psql -U app-user -h localhost app-db < sql/data.sql
```

### Vault

Start the server and grab the root key for initial setup.

```
$ docker-compose up -d vault
$ export VAULT_TOKEN=$(docker-compose logs vault | grep 'Root Token:' | awk '{print $NF}')
$ echo $VAULT_TOKEN
s.29aVhedp1lhasRKB5bmoNWXS
```

Create a key-value secret to store app passwords in, create a policy allowing
read access to the new secret.

```
export VAULT_ADDR=http://localhost:8200/
vault kv put secret/app database_password=acKQfbU9PmKKsWu9
vault policy write app vault/app.hcl
```

Enable approle authentication, create a new role for our application (configured
with short token lifespans), and create a policy for generating login tokens for
the new role.

```
vault auth enable approle
vault write auth/approle/role/app secret_id_ttl=1m token_ttl=1m token_max_tll=1m policies="app"
vault write sys/policy/ar-token-create policy=@vault/ar-token-create.hcl
```

### Application startup

Get the role ID and role token, then template the values into the config file:

```
export ROLE_ID=$(vault read auth/approle/role/app/role-id -field=role_id | grep 'role_id' | awk '{print $2}')
export ROLE_TOKEN=$(vault token-create -policy=ar-token-create)
echo "{\"role_id\":\"$ROLE_ID\", \"role_token\":\"$ROLE_TOKEN\"}" | mustache - app/settings.yml.mustache app/settings.yml
```

Now build the image and start the container. The app will use the given ID and
token to log into the vault server, generate a one time token with which to
retrieve the database password.

```
docker-compose build app
./render-auth.sh
docker-compose up app
```
