# Registry

The registry models unit capabilities and protocol metadata in JSON.

## File

- `units.json`: source-of-truth unit catalog

## Schema shape

Each unit record includes:

- `unit_id`: stable identifier
- `bus`: hardware bus (`i2c`, `spi`, `internal`, etc.)
- `address`: optional bus address
- `capabilities`: list of exposed semantic outputs
- `register_map`: symbolic register/field mapping

## Add a new unit

1. Add a record in `units.json`
2. Keep naming consistent and lowercase
3. Document capability semantics in docs
