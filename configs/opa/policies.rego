package roborouter.policies

default allow = false

# Example baseline policy scaffold; expand in S7.
allow {
  some t
  t := input.export.type
  t == "potree" or t == "laz" or t == "gltf" or t == "webm"
}

deny[msg] {
  not allow
  msg := sprintf("blocked export: type=%v crs=%v", [input.export.type, input.export.crs])
}

