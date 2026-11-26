package laboratorio

permitida := {"services": {"api": {
    "user": "10001:10001",
    "read_only": true,
    "privileged": false,
    "cap_drop": ["ALL"],
    "security_opt": ["no-new-privileges:true"],
    "ports": ["127.0.0.1:8000:8000"]
}}}

test_permite_configuracion_local if {
    allow with input as permitida
}

test_rechaza_escritura if {
    modificada := json.patch(permitida, [{"op": "replace", "path": "/services/api/read_only", "value": false}])
    not allow with input as modificada
}

test_rechaza_ausencia if {
    not allow with input as {}
}
