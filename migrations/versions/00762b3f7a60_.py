"""v3.8: migrate WebAuthn credential algorithm selection

Revision ID: 00762b3f7a60
Revises: 86f40f535d7c
Create Date: 2022-08-31 11:24:12.226997

"""

# revision identifiers, used by Alembic.
revision = "00762b3f7a60"
down_revision = "86f40f535d7c"

import re
from alembic import op
from sqlalchemy import orm, update
from edumfa.models import Policy

old_policy_action = "webauthn_public_key_credential_algorithm_preference"
new_policy_action = "webauthn_public_key_credential_algorithms"
cred_alg_map = {
    "ecdsa_preferred": "ecdsa rsassa-pss",
    "ecdsa_only": "ecdsa",
    "rsassa-pss_preferred": "ecdsa rsassa-pss",
    "rsassa-pss_only": "rsassa-pss",
}


def upgrade():
    # we need to change the enrollment policy action from
    # "webauthn_public_key_credential_algorithm_preference" to
    # "webauthn_public_key_credential_algorithms" and also change the value
    # to directly use the (space separated) algorithms.
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    regex = re.compile(f"^{old_policy_action!s}")
    try:
        for row in session.query(Policy).filter(
            Policy.action.like(f"%{old_policy_action!s}%")
        ):
            # get the current setting
            pol_actions = [x.strip() for x in row.action.split(",")]
            for pol_action in filter(regex.match, pol_actions):
                cred_algs = cred_alg_map[pol_action.split("=")[1]]
                pol_actions.remove(pol_action)
                pol_actions.append(f"{new_policy_action!s}={cred_algs!s}")
            row.action = ", ".join(pol_actions)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error updating the enrollment policy {old_policy_action!s}: {e!s}")


def downgrade():
    # for the downgrade we just use the "ecdsa_preferred" setting
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    regex = re.compile(f"^{new_policy_action!s}")
    try:
        for row in session.query(Policy).filter(
            Policy.action.like(f"%{new_policy_action!s}%")
        ):
            # get the current setting
            pol_actions = [x.strip() for x in row.action.split(",")]
            for pol_action in filter(regex.match, pol_actions):
                pol_actions.remove(pol_action)
                pol_actions.append(f"{old_policy_action!s}=ecdsa_preferred")
            row.action = ", ".join(pol_actions)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error downgrading the enrollment policy {new_policy_action!s}: {e!s}")
    pass
