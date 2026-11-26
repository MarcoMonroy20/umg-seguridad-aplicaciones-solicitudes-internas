package laboratorio

default allow := false

allow if {
    api := input.services.api
    api.user == "10001:10001"
    api.read_only == true
    api.privileged == false
    api.cap_drop == ["ALL"]
    api.security_opt == ["no-new-privileges:true"]
    api.ports == ["127.0.0.1:8000:8000"]
    object.get(api, "volumes", []) == []
    object.get(api, "network_mode", "") == ""
}

permit if allow
