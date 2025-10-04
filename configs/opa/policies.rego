package roborouter.policies

default allow = false

# Example baseline policy scaffold; expand in S7.
allow {
  input.export.type == "potree"
}

