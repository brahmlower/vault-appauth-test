
# Vault Test

s.3eiKdgx89zau6XF2GCenPYTP
vault write auth/approle/role/app secret_id_ttl=2m token_ttl=2m token_max_tll=120m policies="app"

## Initial setup

```
vault policy write -address=http://localhost:8200 app app.hcl
vault auth enable -address="http://localhost:8200" approle
vault write -address="http://localhost:8200" auth/approle/role/app secret_id_ttl=2m token_ttl=2m token_max_tll=120m policies="app"
```

## Application configuration

```
vault write -address="http://localhost:8200" -f auth/approle/role/app/secret-id
vault write auth/approle/login role_id=4105f0ec-b369-10a3-cbd7-87ff0aca1443 secret_id=a4d00a55-9882-c2e2-7a04-d21bc6eb12d6
```

## Build

```
vault read -address=http://localhost:8200 -format=json -field=data auth/approle/role/app/role-id | mustache - app/settings.yml app/settings.out.yml

```