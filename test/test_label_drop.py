from neomodel import StructuredNode, StringProperty, config
from neomodel.core import db, remove_all_labels
from neo4j.exceptions import ClientError

from test.utils import get_db_constraints_as_dict, get_db_indexes_as_dict

config.AUTO_INSTALL_LABELS = True


class ConstraintAndIndex(StructuredNode):
    name = StringProperty(unique_index=True)
    last_name = StringProperty(index=True)


def test_drop_labels():
    constraints_before = get_db_constraints_as_dict()
    indexes_before = get_db_indexes_as_dict()

    assert len(constraints_before) > 0
    assert len(indexes_before) > 0

    remove_all_labels()

    constraints = get_db_constraints_as_dict()
    indexes = get_db_indexes_as_dict()

    assert len(constraints) == 0
    # Ignore the automatically created LOOKUP indexes
    assert len([index for index in indexes if index["labelsOrTypes"]]) == 0

    # Recreating all old constraints and indexes
    for constraint in constraints_before:
        constraint_type_clause = "UNIQUE"
        if constraint["type"] == "NODE_PROPERTY_EXISTENCE":
            constraint_type_clause = "NOT NULL"
        elif constraint["type"] == "NODE_KEY":
            constraint_type_clause = "NODE KEY"

        db.cypher_query('CREATE CONSTRAINT {0} FOR (n:{1}) REQUIRE n.{2} IS {3}'
            .format
            (
                constraint["name"],
                constraint["labelsOrTypes"][0],
                constraint["properties"][0],
                constraint_type_clause,
            ))
    for index in indexes_before:
        try:
            # Ignore the automatically created LOOKUP indexes
            if index["labelsOrTypes"] is None or index["labelsOrTypes"] == []:
                continue
            db.cypher_query('CREATE INDEX {0} FOR (n:{1}) ON (n.{2})'.format(index["name"], index["labelsOrTypes"][0], index["properties"][0]))
        except ClientError:
            pass
