"""V1 substitutions cannot reuse a COUNT requirement's item identity.

Revision ID: 0006
Revises: 0005
Frozen SQL; supplemental policy guard only. Existing seal/version functions are unchanged.
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

LOCK = (
    "LOCK TABLE recipe_versions, recipe_ingredients, recipe_variant_rules, "
    "recipe_version_seals IN ACCESS EXCLUSIVE MODE"
)

PREFLIGHT = """
DO $$ BEGIN
 IF EXISTS (
  SELECT 1 FROM recipe_variant_rules r JOIN recipe_ingredients i
   ON (i.id,i.recipe_version_id)=(r.requirement_id,r.recipe_version_id)
  WHERE i.basis='COUNT'
 ) THEN
  RAISE EXCEPTION '0006: legacy COUNT substitutions need explicit archival/correction'
   USING ERRCODE='23514';
 END IF;
END $$;
"""

GUARD = """
CREATE FUNCTION menuto_recipe_count_substitution_policy() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (
  SELECT 1 FROM recipe_variant_rules r JOIN recipe_ingredients i
   ON (i.id,i.recipe_version_id)=(r.requirement_id,r.recipe_version_id)
  WHERE r.recipe_version_id=NEW.recipe_version_id AND i.basis='COUNT'
 ) THEN
  RAISE EXCEPTION 'V1 COUNT substitution requires deferred replacement count identity'
   USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE TRIGGER recipe_version_count_substitution_check
 BEFORE INSERT ON recipe_version_seals FOR EACH ROW
 EXECUTE FUNCTION menuto_recipe_count_substitution_policy();
"""


def upgrade():
    op.execute(LOCK)
    op.execute(PREFLIGHT)
    op.execute(GUARD)


def downgrade():
    # Removing this additive policy loses no rows, columns or provenance.
    op.execute(LOCK)
    op.execute("DROP TRIGGER recipe_version_count_substitution_check ON recipe_version_seals")
    op.execute("DROP FUNCTION menuto_recipe_count_substitution_policy()")
