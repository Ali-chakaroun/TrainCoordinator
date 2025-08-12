from rdflib import Graph, Namespace, RDF
from rdflib.collection import Collection

ODRL = Namespace("http://www.w3.org/ns/odrl/2/")
EX = Namespace("http://example.org/")

def get_local_name(uri):
    return uri.split("/")[-1]

def is_access_allowed(policy_file, assignee_uri, action, target_uri, constraints):
    g = Graph()
    g.parse(policy_file, format="turtle")

    for policy in g.subjects(RDF.type, ODRL.Offer):
        for perm in g.objects(policy, ODRL.permission):
            if (
                str(g.value(perm, ODRL.assignee)) == assignee_uri and
                str(g.value(perm, ODRL.action)) == action and
                any(str(t) == target_uri for t in g.objects(perm, ODRL.target))
            ):
                # --- Extract RDF and SPARQL target files
                data_file = None
                for t in g.objects(perm, ODRL.target):
                    t_str = str(t)
                    if "/sparql/" in t_str:
                        data_file = t_str.split("/sparql/")[-1] + ".txt"

                if not data_file:
                    return None

                # --- Collect allowed constraint keys (if any)
                allowed_keys = set()
                for c in g.objects(perm, ODRL.constraint):
                    left = g.value(c, ODRL.leftOperand)
                    if left:
                        allowed_keys.add(get_local_name(str(left)))
                for prohibition in g.objects(policy, ODRL.prohibition):
                    for c in g.objects(prohibition, ODRL.constraint):
                        left = g.value(c, ODRL.leftOperand)
                        if left:
                            allowed_keys.add(get_local_name(str(left)))

                # --- Reject request with unknown constraints only if policy defines allowed keys
                request_keys = set(constraints.keys())

                if not request_keys.issuperset(allowed_keys):
                    return None

                # --- Also reject if the request includes constraints not in the policy
                if not allowed_keys.issuperset(request_keys):
                    return None
                has_prohibitions = any(g.objects(policy, ODRL.prohibition))
                if not constraints and has_prohibitions:
                    return None
                # --- Prohibition logic: deny if any constraints in a prohibition match
                for prohibition in g.objects(policy, ODRL.prohibition):
                    if str(g.value(prohibition, ODRL.action)) != action:
                        continue

                    for c in g.objects(prohibition, ODRL.constraint):
                        left = g.value(c, ODRL.leftOperand)
                        right = g.value(c, ODRL.rightOperand)
                        key = get_local_name(str(left))
                        policy_vals = [str(v).lower() for v in Collection(g, right)]

                        req_vals = constraints.get(key)
                        if not req_vals:
                            continue
                        
                        req_vals_lower = [v.lower() for v in req_vals]

                        #If ANY request value matches the prohibited list then DENY
                        if any(req_val in policy_vals for req_val in req_vals_lower):
                            return None

                return data_file
                
    return None