import os

import rdflib
from rdflib import BNode, URIRef, Graph, Namespace, Literal
from rdflib import OWL, RDF, RDFS, XSD, TIME

# Prefixes
base_prefix = "kastle"
name_space = "https://kastle-labl.org/"
pfs = {
f"{base_prefix}r": Namespace(f"{name_space}lod/resource/"),
f"{base_prefix}-ont": Namespace(f"{name_space}lod/ontology/"),
"geo": Namespace("http://www.opengis.net/ont/geosparql#"),
"geof": Namespace("http://www.opengis.net/def/function/geosparql/"),
"sf": Namespace("http://www.opengis.net/ont/sf#"),
"wd": Namespace("http://www.wikidata.org/entity/"),
"wdt": Namespace("http://www.wikidata.org/prop/direct/"),
"dbo": Namespace("http://dbpedia.org/ontology/"),
"time": Namespace("http://www.w3.org/2006/time#"),
"ssn": Namespace("http://www.w3.org/ns/ssn/"),
"sosa": Namespace("http://www.w3.org/ns/sosa/"),
"cdt": Namespace("http://w3id.org/lindt/custom_datatypes#"),
"ex": Namespace("https://example.com/")
}
# Initialization shortcut
def init_kg(prefixes=pfs):
    kg = Graph()
    for prefix in pfs:
        kg.bind(prefix, pfs[prefix])
    return kg
g = init_kg()

# Conveniences
a = RDF["type"]
sco = RDFS["subClassOf"]
ont_ns = pfs[f"{base_prefix}-ont"]
r_ns = pfs[f"{base_prefix}r"]
owl_some = OWL.someValuesFrom
owl_all = OWL.allValuesFrom

############### LOGICIAN START
input_file = "example/test.opal"

if not os.path.exists("output"):
	os.makedirs("output")
output_file = "output/output.ttl"

###############
quant_types = {"exists": OWL.someValuesFrom, "forall": OWL.allValuesFrom}
card_types  = {"min": OWL.minQualifiedCardinality, "max": OWL.maxQualifiedCardinality, "exact": OWL.qualifiedCardinality}

def create_restriction_node(pred, target, quant, g=g):
	# create the blank node which shall act as the restriction
	restriction_node = BNode()
	# declare its type (i.e., it's a restriction -- the point of this function)
	g.add( (restriction_node, a, OWL.Restriction) )
	# which property its acting on
	g.add( (restriction_node, OWL.onProperty, pred) )
	# the nature of the restriction
	try:
		if(target.find('xsd') == -1):
			g.add( (restriction_node, quant_types[quant], target) )
		else:
			lhs = target.split("/")[-1].split(":")[0]
			rhs = target.split("/")[-1].split(":")[1]
			g.add( (restriction_node, quant_types[quant], pfs[lhs][rhs]) )
	except KeyError as e:
		raise Exception(f"Illegal restriction type: {quant}")

	return restriction_node

def create_inverse_prop(pred):
	iprop = BNode()
	g.add( (iprop, OWL.inverseOf, pred) )
	return iprop

def create_cardinality_node(pred, card_type, cardinality, ont_o):
	# create the blank node which shall act as the restriction
	restriction_node = BNode()
	# declare its type (i.e., it's a restriction -- the point of this function)
	g.add( (restriction_node, a, OWL.Restriction) )
	# which property its acting on
	g.add( (restriction_node, OWL.onProperty, pred) )
	# Add the cardinality value
	g.add( (restriction_node, card_types[card_type], Literal(cardinality, datatype=XSD.nonNegativeInteger)) )
		
	# What is being restricted?
	if(ont_o.find('xsd') == -1):
		g.add( (restriction_node, OWL.onClass, ont_o) )
	else:
		lhs = ont_o.split("/")[-1].split(":")[0]
		rhs = ont_o.split("/")[-1].split(":")[1]
		g.add( (restriction_node, OWL.onDataRange, pfs[lhs][rhs]) )
		
	return restriction_node

with open(input_file, "r") as f:
	views = [line.strip() for line in f.readlines() if not line[0] == "#"]

	for view in views:
		s, p, o, *ax_types = view.split(" ")
		## create uris
		ont_s = ont_ns[s]
		ont_o = ont_ns[o]

		g.add( (ont_s, a, OWL.Class))

		if(o.find('xsd') != -1):
			g.add( ( ont_ns[p], a, OWL.DatatypeProperty ) )
		else:
			if(p != "sco"):
				g.add( (ont_ns[p], a, OWL.ObjectProperty) )
			g.add( (ont_o, a, OWL.Class) )

		if p == "sco": 
			g.add( (ont_s, sco, ont_o) )
		else:
			ont_p = ont_ns[p]
			for line_no, ax_type in enumerate(ax_types, start=1):
				if ax_type not in ["dj", "d", "sd", "r", "sr", "e", "ie", "uie", "f", "qf", "sf", "qsf", "if", "iqf", "isf", "iqsf", "st"]:
					raise Exception(f"Illegal axiom type at Line {line_no}: {ax_type}.")

				if ax_type == "dj":
					pass
					# g.add( () )
				
				# Domain
				if ax_type == "d":
					lhs = create_restriction_node(ont_p, OWL.Thing, "exists", g)
					g.add( (lhs, sco, ont_s) )
				
				# Scoped Domain
				if ax_type == "sd":
					lhs = create_restriction_node(ont_p, ont_s, "exists", g)
					g.add( (lhs, sco, ont_s) )
				
				# Range
				if ax_type == "r":
					rhs = create_restriction_node(ont_p, ont_o, "forall", g)
					g.add( (OWL.Thing, sco, rhs) )
				
				# Scoped Range
				if ax_type == "sr":
					rhs = create_restriction_node(ont_p, ont_o, "forall", g)
					g.add( (ont_s, sco, rhs) )
				
				# Existential
				if ax_type == "e":
					rhs = create_restriction_node(ont_p, ont_o, "exists", g)
					g.add( (ont_s, sco, rhs) )
				
				# Inverse Existential
				if ax_type == "ie":
					inverse_p = create_inverse_prop(ont_p, g)
					rhs = create_restriction_node(inverse_p, ont_o, "exists", g)
					g.add( (ont_s, sco, rhs) )

				if ax_type == "uie":
					pass
				
				# Functional
				if ax_type == "f":
					rhs = create_cardinality_node(ont_p, "max", 1, OWL.Thing, g)
					g.add( (OWL.Thing, sco, rhs) )
				
				# Qualified Functional
				if ax_type == "qf":
					rhs = create_cardinality_node(ont_p, "max", 1, ont_o, g)
					g.add( (OWL.Thing, sco, rhs) )
				
				# Scoped Functional
				if ax_type == "sf":
					rhs = create_cardinality_node(ont_p, "max", 1, OWL.Thing, g)
					g.add( (ont_s, sco, rhs) )
				
				# Qualified Scoped Functional
				if ax_type == "qsf":
					rhs = create_cardinality_node(ont_p, "max", 1, ont_o, g)
					g.add( (ont_s, sco, rhs) )
				
				# Inverse Functional
				if ax_type == "if":
					inverse_p = create_inverse_prop(ont_p, g)
					rhs = create_cardinality_node(inverse_p, "max", 1, OWL.Thing, g)
					g.add( (OWL.Thing, sco, rhs) )
				
				# Inverse Qualified Functional
				if ax_type == "iqf":
					inverse_p = create_inverse_prop(ont_p, g)
					rhs = create_cardinality_node(inverse_p, "max", 1, ont_o, g)
					g.add( (OWL.Thing, sco, rhs) )
				
				# Inverse Scoped Functional
				if ax_type == "isf":
					inverse_p = create_inverse_prop(ont_p, g)
					rhs = create_cardinality_node(inverse_p, "max", 1, OWL.Thing, g)
					g.add( (ont_s, sco, rhs) )
				
				# Inverse Qualified Scoped Functional
				if ax_type == "iqsf":
					inverse_p = create_inverse_prop(ont_p, g)
					rhs = create_cardinality_node(inverse_p, "max", 1, ont_o, g)
					g.add( (ont_s, sco, rhs) )
				
				# Structural Tautology
				if ax_type == "st":
					rhs = create_cardinality_node(ont_p, "min", 0, ont_o, g)
					g.add( (ont_s, sco, rhs) )


temp = g.serialize(format="turtle", encoding="utf-8", destination=output_file)