from rdflib import Graph, Namespace, RDF
from rdflib.collection import Collection

ODRL = Namespace("http://www.w3.org/ns/odrl/2/")
EX = Namespace("http://example.org/")

def get_local_name(uri):
    return uri.split("/")[-1]

def parse_request(turtle_string):
    g = Graph()
    g.parse(data=turtle_string, format="turtle")

    for req in g.subjects(RDF.type, ODRL.Request):
        permission = g.value(req, ODRL.permission)
        if not permission:
            continue

        assignee = g.value(permission, ODRL.assignee)
        action = g.value(permission, ODRL.action)
        target = g.value(permission, ODRL.target)

        data = {
            "assignee": str(assignee),
            "action": str(action),
            "target": str(target),
            "constraints": {}
        }

        for constraint in g.objects(permission, ODRL.constraint):
            left = g.value(constraint, ODRL.leftOperand)
            right = g.value(constraint, ODRL.rightOperand)

            key = get_local_name(str(left))
            values = [str(v) for v in Collection(g, right)]
            data["constraints"][key] = values

        return data

    return None
