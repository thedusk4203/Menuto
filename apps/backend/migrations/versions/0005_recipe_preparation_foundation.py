"""Recipe / Preparation immutable authored foundation (ADR-005/010).

Revision ID: 0005
Revises: 0004
Frozen PostgreSQL DDL/SQL; no mutable ORM metadata import.
"""

# ruff: noqa: E501 -- frozen DDL and trigger SQL
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABLES = (
    "recipes",
    "recipe_versions",
    "recipe_ingredients",
    "recipe_portion_tiers",
    "recipe_tier_quantities",
    "recipe_variant_rules",
    "recipe_rule_combinations",
    "recipe_combination_members",
    "preparation_transformations",
    "recipe_version_seals",
)

DDL = (
    """CREATE TABLE recipes (
	name VARCHAR(200) NOT NULL, 
	cooking_method VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_recipes PRIMARY KEY (id), 
	CONSTRAINT ck_recipes_cooking_method CHECK (cooking_method ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipes_name CHECK (length(trim(name))>0)
)""",
    """CREATE TABLE recipe_versions (
	recipe_id UUID NOT NULL, 
	authored_transaction VARCHAR(30) DEFAULT pg_current_xact_id()::text NOT NULL, 
	version INTEGER NOT NULL, 
	serving_definition VARCHAR(100) NOT NULL, 
	serving_description VARCHAR(200) NOT NULL, 
	base_servings NUMERIC NOT NULL, 
	procedure TEXT NOT NULL, 
	review_status VARCHAR(20) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_recipe_versions PRIMARY KEY (id), 
	CONSTRAINT ck_recipe_versions_source_kind CHECK (source_kind IN ('USER_AUTHORED','CURATED_REFERENCE','IMPORTED_DRAFT')), 
	CONSTRAINT ck_recipe_versions_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_versions_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_recipe_versions_observed_at CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_recipe_versions_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_recipe_versions_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_recipe_versions_source_system_external_record_id_sou_976c UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_recipe_versions_recipe_id_version UNIQUE (recipe_id, version), 
	CONSTRAINT ck_recipe_versions_version CHECK (version>0), 
	CONSTRAINT ck_recipe_versions_serving_definition CHECK (serving_definition ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_versions_serving_description CHECK (length(trim(serving_description))>0), 
	CONSTRAINT ck_recipe_versions_procedure CHECK (length(trim(procedure))>0 AND length(procedure)<=100000), 
	CONSTRAINT ck_recipe_versions_base_servings_numeric CHECK (abs(base_servings) < 1000000000000 AND base_servings = trunc(base_servings,6) AND base_servings>0), 
	CONSTRAINT ck_recipe_versions_review CHECK (review_status IN ('DRAFT','REVIEWED') AND (source_kind!='IMPORTED_DRAFT' OR review_status='DRAFT')), 
	CONSTRAINT fk_recipe_versions_recipe_id_recipes FOREIGN KEY(recipe_id) REFERENCES recipes (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_ingredients (
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	slot VARCHAR(100) NOT NULL, 
	ingredient_id UUID NOT NULL, 
	amount NUMERIC NOT NULL, 
	basis VARCHAR(20) NOT NULL, 
	item_ref VARCHAR(100), 
	role VARCHAR(100) NOT NULL, 
	scaling_kind VARCHAR(20) NOT NULL, 
	scaling_quantum NUMERIC, 
	scaling_minimum NUMERIC, 
	scaling_maximum NUMERIC, 
	adjustment_kind VARCHAR(20) NOT NULL, 
	min_delta NUMERIC NOT NULL, 
	max_delta NUMERIC NOT NULL, 
	adjustment_step NUMERIC, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_recipe_ingredients PRIMARY KEY (id), 
	CONSTRAINT uq_recipe_ingredients_id_recipe_version_id UNIQUE (id, recipe_version_id), 
	CONSTRAINT uq_recipe_ingredients_recipe_version_id_slot UNIQUE (recipe_version_id, slot), 
	CONSTRAINT uq_recipe_ingredients_recipe_version_id_ordinal UNIQUE (recipe_version_id, ordinal), 
	CONSTRAINT ck_recipe_ingredients_slot CHECK (slot ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_ingredients_role CHECK (role ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_ingredients_ordinal CHECK (ordinal>=0), 
	CONSTRAINT ck_recipe_ingredients_amount_numeric CHECK (abs(amount) < 1000000000000 AND amount = trunc(amount,6) AND amount>0), 
	CONSTRAINT ck_recipe_ingredients_quantity_basis CHECK ((basis IN ('EP_RAW_G','COOKED_G') AND item_ref IS NULL) OR (basis='COUNT' AND item_ref IS NOT NULL AND item_ref ~ '^[A-Za-z0-9_.:-]+$')), 
	CONSTRAINT ck_recipe_ingredients_scaling_kind CHECK (scaling_kind IN ('LINEAR','SUBLINEAR','FIXED','DISCRETE','TO_TASTE')), 
	CONSTRAINT ck_recipe_ingredients_scaling_quantum_numeric CHECK (abs(scaling_quantum) < 1000000000000 AND scaling_quantum = trunc(scaling_quantum,6) AND scaling_quantum>0), 
	CONSTRAINT ck_recipe_ingredients_scaling_minimum_numeric CHECK (abs(scaling_minimum) < 1000000000000 AND scaling_minimum = trunc(scaling_minimum,6) AND scaling_minimum>0), 
	CONSTRAINT ck_recipe_ingredients_scaling_maximum_numeric CHECK (abs(scaling_maximum) < 1000000000000 AND scaling_maximum = trunc(scaling_maximum,6) AND scaling_maximum>0), 
	CONSTRAINT ck_recipe_ingredients_scaling_shape CHECK ((scaling_kind='DISCRETE') = (scaling_quantum IS NOT NULL) AND ((scaling_kind='TO_TASTE' AND scaling_minimum IS NOT NULL AND scaling_maximum IS NOT NULL AND scaling_minimum<=scaling_maximum) OR (scaling_kind!='TO_TASTE' AND scaling_minimum IS NULL AND scaling_maximum IS NULL))), 
	CONSTRAINT ck_recipe_ingredients_adjustment_kind CHECK (adjustment_kind IN ('NONE','SMALL','PORTIONABLE','DISCRETE')), 
	CONSTRAINT ck_recipe_ingredients_min_delta_numeric CHECK (abs(min_delta) < 1000000000000 AND min_delta = trunc(min_delta,6)), 
	CONSTRAINT ck_recipe_ingredients_max_delta_numeric CHECK (abs(max_delta) < 1000000000000 AND max_delta = trunc(max_delta,6)), 
	CONSTRAINT ck_recipe_ingredients_adjustment_step_numeric CHECK (abs(adjustment_step) < 1000000000000 AND adjustment_step = trunc(adjustment_step,6) AND adjustment_step>0), 
	CONSTRAINT ck_recipe_ingredients_adjustment_shape CHECK (min_delta<=0 AND max_delta>=0 AND ((adjustment_kind='NONE' AND min_delta=0 AND max_delta=0) OR (adjustment_kind!='NONE' AND min_delta<max_delta)) AND (adjustment_kind!='SMALL' OR min_delta=-max_delta) AND ((adjustment_kind='DISCRETE' AND adjustment_step IS NOT NULL AND mod(min_delta,adjustment_step)=0 AND mod(max_delta,adjustment_step)=0) OR (adjustment_kind!='DISCRETE' AND adjustment_step IS NULL))), 
	CONSTRAINT fk_recipe_ingredients_recipe_version_id_recipe_versions FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_recipe_ingredients_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_portion_tiers (
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	servings NUMERIC NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_recipe_portion_tiers PRIMARY KEY (id), 
	CONSTRAINT uq_recipe_portion_tiers_id_recipe_version_id UNIQUE (id, recipe_version_id), 
	CONSTRAINT uq_recipe_portion_tiers_recipe_version_id_key UNIQUE (recipe_version_id, key), 
	CONSTRAINT uq_recipe_portion_tiers_recipe_version_id_servings UNIQUE (recipe_version_id, servings), 
	CONSTRAINT uq_recipe_portion_tiers_recipe_version_id_ordinal UNIQUE (recipe_version_id, ordinal), 
	CONSTRAINT ck_recipe_portion_tiers_key CHECK (key ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_portion_tiers_servings_numeric CHECK (abs(servings) < 1000000000000 AND servings = trunc(servings,6) AND servings>0), 
	CONSTRAINT ck_recipe_portion_tiers_ordinal CHECK (ordinal>=0), 
	CONSTRAINT fk_recipe_portion_tiers_recipe_version_id_recipe_versions FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_tier_quantities (
	tier_id UUID NOT NULL, 
	requirement_id UUID NOT NULL, 
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	amount NUMERIC NOT NULL, 
	CONSTRAINT pk_recipe_tier_quantities PRIMARY KEY (tier_id, requirement_id), 
	CONSTRAINT fk_recipe_917469a70a9f42f3 FOREIGN KEY(tier_id, recipe_version_id) REFERENCES recipe_portion_tiers (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_recipe_e17a2f26939c6fcc FOREIGN KEY(requirement_id, recipe_version_id) REFERENCES recipe_ingredients (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_recipe_tier_quantities_tier_id_ordinal UNIQUE (tier_id, ordinal), 
	CONSTRAINT ck_recipe_tier_quantities_amount_numeric CHECK (abs(amount) < 1000000000000 AND amount = trunc(amount,6) AND amount>0), 
	CONSTRAINT ck_recipe_tier_quantities_ordinal CHECK (ordinal>=0)
)""",
    """CREATE TABLE recipe_variant_rules (
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	requirement_id UUID NOT NULL, 
	replacement_ingredient_id UUID NOT NULL, 
	quantity_factor NUMERIC NOT NULL, 
	structural BOOLEAN NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_recipe_variant_rules PRIMARY KEY (id), 
	CONSTRAINT ck_recipe_variant_rules_source_kind CHECK (source_kind IN ('USER_AUTHORED','CURATED_REFERENCE','IMPORTED_DRAFT')), 
	CONSTRAINT ck_recipe_variant_rules_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_variant_rules_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_recipe_variant_rules_observed_at CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_recipe_variant_rules_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_recipe_variant_rules_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_recipe_variant_rules_source_system_external_record_i_c75b UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_recipe_variant_rules_id_recipe_version_id UNIQUE (id, recipe_version_id), 
	CONSTRAINT uq_recipe_variant_rules_recipe_version_id_key UNIQUE (recipe_version_id, key), 
	CONSTRAINT uq_recipe_variant_rules_recipe_version_id_ordinal UNIQUE (recipe_version_id, ordinal), 
	CONSTRAINT fk_recipe_e17a2f26939c6fcc FOREIGN KEY(requirement_id, recipe_version_id) REFERENCES recipe_ingredients (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_recipe_variant_rules_key CHECK (key ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_variant_rules_version_ordinal CHECK (version>0 AND ordinal>=0), 
	CONSTRAINT ck_recipe_variant_rules_quantity_factor_numeric CHECK (abs(quantity_factor) < 1000000000000 AND quantity_factor = trunc(quantity_factor,6) AND quantity_factor>0), 
	CONSTRAINT fk_recipe_variant_rules_replacement_ingredient_id_ingredients FOREIGN KEY(replacement_ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_rule_combinations (
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	key VARCHAR(100) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_recipe_rule_combinations PRIMARY KEY (id), 
	CONSTRAINT ck_recipe_rule_combinations_source_kind CHECK (source_kind IN ('USER_AUTHORED','CURATED_REFERENCE','IMPORTED_DRAFT')), 
	CONSTRAINT ck_recipe_rule_combinations_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_rule_combinations_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_recipe_rule_combinations_observed_at CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_recipe_rule_combinations_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_recipe_rule_combinations_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_recipe_rule_combinations_source_system_external_reco_3dfc UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_recipe_rule_combinations_id_recipe_version_id UNIQUE (id, recipe_version_id), 
	CONSTRAINT uq_recipe_rule_combinations_recipe_version_id_key UNIQUE (recipe_version_id, key), 
	CONSTRAINT uq_recipe_rule_combinations_recipe_version_id_ordinal UNIQUE (recipe_version_id, ordinal), 
	CONSTRAINT ck_recipe_rule_combinations_key CHECK (key ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_recipe_rule_combinations_ordinal CHECK (ordinal>=0), 
	CONSTRAINT fk_recipe_rule_combinations_recipe_version_id_recipe_versions FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_combination_members (
	combination_id UUID NOT NULL, 
	rule_id UUID NOT NULL, 
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	CONSTRAINT pk_recipe_combination_members PRIMARY KEY (combination_id, rule_id), 
	CONSTRAINT fk_recipe_4b5242a920dd0050 FOREIGN KEY(combination_id, recipe_version_id) REFERENCES recipe_rule_combinations (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT fk_recipe_28918e752c71b20e FOREIGN KEY(rule_id, recipe_version_id) REFERENCES recipe_variant_rules (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT uq_recipe_combination_members_combination_id_ordinal UNIQUE (combination_id, ordinal), 
	CONSTRAINT ck_recipe_combination_members_ordinal CHECK (ordinal>=0)
)""",
    """CREATE TABLE preparation_transformations (
	recipe_version_id UUID NOT NULL, 
	ordinal INTEGER NOT NULL, 
	requirement_id UUID NOT NULL, 
	ingredient_id UUID NOT NULL, 
	preparation_key VARCHAR(100) NOT NULL, 
	method VARCHAR(100) NOT NULL, 
	version INTEGER NOT NULL, 
	source_basis VARCHAR(20) NOT NULL, 
	target_basis VARCHAR(20) NOT NULL, 
	factor NUMERIC NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	source_kind VARCHAR(30) NOT NULL, 
	source_system VARCHAR(100) NOT NULL, 
	external_record_id VARCHAR(2048) NOT NULL, 
	source_version VARCHAR(200) NOT NULL, 
	source_uri VARCHAR(2048), 
	content_hash VARCHAR(64), 
	observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	CONSTRAINT pk_preparation_transformations PRIMARY KEY (id), 
	CONSTRAINT ck_preparation_transformations_source_kind CHECK (source_kind IN ('USER_AUTHORED','CURATED_REFERENCE','IMPORTED_DRAFT')), 
	CONSTRAINT ck_preparation_transformations_source_system CHECK (source_system ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_preparation_transformations_source_identity CHECK (length(trim(external_record_id))>0 AND length(trim(source_version))>0 AND external_record_id !~ '[[:cntrl:]]' AND source_version !~ '[[:cntrl:]]'), 
	CONSTRAINT ck_preparation_transformations_observed_at CHECK (isfinite(observed_at)), 
	CONSTRAINT ck_preparation_transformations_content_hash CHECK (content_hash IS NULL OR content_hash ~ '^[a-f0-9]{64}$'), 
	CONSTRAINT ck_preparation_transformations_source_uri CHECK (source_uri IS NULL OR (source_uri ~ '^https?://[^/@[:space:]]+([/:?#]|$)' AND source_uri !~ '^https?://[^/]*@' AND source_uri !~ '[[:cntrl:]]')), 
	CONSTRAINT uq_preparation_transformations_source_system_external_r_20a6 UNIQUE (source_system, external_record_id, source_version), 
	CONSTRAINT uq_preparation_transformations_recipe_version_id_requir_4b5a UNIQUE (recipe_version_id, requirement_id, ingredient_id), 
	CONSTRAINT uq_preparation_transformations_recipe_version_id_ordinal UNIQUE (recipe_version_id, ordinal), 
	CONSTRAINT fk_recipe_e17a2f26939c6fcc FOREIGN KEY(requirement_id, recipe_version_id) REFERENCES recipe_ingredients (id, recipe_version_id) ON DELETE RESTRICT, 
	CONSTRAINT ck_preparation_transformations_preparation_key CHECK (preparation_key ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_preparation_transformations_method CHECK (method ~ '^[A-Za-z0-9_.:-]+$'), 
	CONSTRAINT ck_preparation_transformations_version_ordinal CHECK (version>0 AND ordinal>=0), 
	CONSTRAINT ck_preparation_transformations_yield_chain CHECK (source_basis='EP_RAW_G' AND target_basis='COOKED_G'), 
	CONSTRAINT ck_preparation_transformations_factor_numeric CHECK (abs(factor) < 1000000000000 AND factor = trunc(factor,6) AND factor>0), 
	CONSTRAINT fk_preparation_transformations_ingredient_id_ingredients FOREIGN KEY(ingredient_id) REFERENCES ingredients (id) ON DELETE RESTRICT
)""",
    """CREATE TABLE recipe_version_seals (
	recipe_version_id UUID NOT NULL, 
	CONSTRAINT pk_recipe_version_seals PRIMARY KEY (recipe_version_id), 
	CONSTRAINT fk_recipe_version_seals_recipe_version_id_recipe_versions FOREIGN KEY(recipe_version_id) REFERENCES recipe_versions (id) ON DELETE RESTRICT
)""",
    """ALTER TABLE recipe_versions ADD CONSTRAINT fk_recipe_version_required_seal FOREIGN KEY(id) REFERENCES recipe_version_seals (recipe_version_id) DEFERRABLE INITIALLY DEFERRED""",
)

TRIGGERS = r"""
CREATE FUNCTION menuto_recipe_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'Recipe authored facts are immutable; create a new RecipeVersion'
 USING ERRCODE='23514';
END $$;

CREATE FUNCTION menuto_recipe_child_insert() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE assembly_transaction text;
BEGIN
 -- Serializes seal/child insertion even when writers use direct SQL.
 SELECT authored_transaction INTO assembly_transaction FROM recipe_versions
 WHERE id=NEW.recipe_version_id FOR UPDATE;
 IF assembly_transaction IS DISTINCT FROM pg_current_xact_id()::text THEN
  RAISE EXCEPTION 'RecipeVersion assembly transaction is closed' USING ERRCODE='23514';
 END IF;
 IF EXISTS (SELECT 1 FROM recipe_version_seals WHERE recipe_version_id=NEW.recipe_version_id) THEN
  RAISE EXCEPTION 'RecipeVersion already sealed' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_recipe_begin_version() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 NEW.authored_transaction := pg_current_xact_id()::text;
 RETURN NEW;
END $$;

CREATE FUNCTION menuto_recipe_seal() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v recipe_versions%ROWTYPE;
BEGIN
 SELECT * INTO STRICT v FROM recipe_versions WHERE id=NEW.recipe_version_id FOR UPDATE;
 IF NOT EXISTS (SELECT 1 FROM recipe_ingredients WHERE recipe_version_id=v.id)
 OR NOT EXISTS (SELECT 1 FROM recipe_portion_tiers WHERE recipe_version_id=v.id AND servings=v.base_servings)
 OR EXISTS (
  SELECT 1 FROM recipe_portion_tiers t CROSS JOIN recipe_ingredients i
  WHERE t.recipe_version_id=v.id AND i.recipe_version_id=v.id AND NOT EXISTS (
   SELECT 1 FROM recipe_tier_quantities q WHERE q.tier_id=t.id AND q.requirement_id=i.id)
 ) THEN
  RAISE EXCEPTION 'Incomplete ingredient/tier aggregate' USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM recipe_tier_quantities q
  JOIN recipe_ingredients i ON i.id=q.requirement_id
  JOIN recipe_portion_tiers t ON t.id=q.tier_id
  WHERE q.recipe_version_id=v.id AND (
   (t.servings=v.base_servings AND q.amount!=i.amount)
   OR (i.scaling_kind='LINEAR' AND q.amount*v.base_servings!=i.amount*t.servings)
   OR (i.scaling_kind='FIXED' AND q.amount!=i.amount)
   OR (i.scaling_kind='TO_TASTE' AND (q.amount<i.scaling_minimum OR q.amount>i.scaling_maximum))
  )
 ) THEN
  RAISE EXCEPTION 'Tier violates authored scaling policy' USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM recipe_ingredients i
  JOIN recipe_tier_quantities a ON a.requirement_id=i.id
  JOIN recipe_portion_tiers ta ON ta.id=a.tier_id
  JOIN recipe_tier_quantities b ON b.requirement_id=i.id
  JOIN recipe_portion_tiers tb ON tb.id=b.tier_id
  WHERE i.recipe_version_id=v.id AND i.scaling_kind='SUBLINEAR' AND ta.servings<tb.servings
  AND (a.amount>=b.amount OR b.amount*ta.servings>=a.amount*tb.servings)
 ) THEN
  RAISE EXCEPTION 'SUBLINEAR requires monotonic less-than-proportional authored points'
  USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM recipe_ingredients i
  JOIN recipe_tier_quantities q ON q.requirement_id=i.id
  CROSS JOIN LATERAL (
    SELECT 1::numeric AS factor UNION ALL
    SELECT r.quantity_factor FROM recipe_variant_rules r WHERE r.requirement_id=i.id
  ) factors
  WHERE i.recipe_version_id=v.id AND (
   q.amount*factors.factor+i.min_delta<=0
   OR (i.scaling_kind='DISCRETE' AND (
    mod(q.amount*factors.factor,i.scaling_quantum)!=0
    OR mod(i.min_delta,i.scaling_quantum)!=0 OR mod(i.max_delta,i.scaling_quantum)!=0
    OR (i.adjustment_kind!='NONE' AND (
     i.adjustment_kind!='DISCRETE' OR mod(i.adjustment_step,i.scaling_quantum)!=0))
   ))
  )
 ) THEN
  RAISE EXCEPTION 'Binding violates positivity or discrete quantity envelope' USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM recipe_variant_rules r JOIN recipe_ingredients i ON i.id=r.requirement_id
  WHERE r.recipe_version_id=v.id AND r.replacement_ingredient_id=i.ingredient_id
 ) THEN
  RAISE EXCEPTION 'Substitution must change ingredient' USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM recipe_rule_combinations c WHERE c.recipe_version_id=v.id AND (
   (SELECT count(*) FROM recipe_combination_members m WHERE m.combination_id=c.id)<2
   OR (SELECT count(*) FROM recipe_combination_members m WHERE m.combination_id=c.id) !=
      (SELECT count(DISTINCT r.requirement_id) FROM recipe_combination_members m
       JOIN recipe_variant_rules r ON r.id=m.rule_id WHERE m.combination_id=c.id)
  )
 ) THEN
  RAISE EXCEPTION 'Combination needs distinct authored slots and at least two rules' USING ERRCODE='23514';
 END IF;
 IF EXISTS (
  SELECT 1 FROM preparation_transformations p JOIN recipe_ingredients i ON i.id=p.requirement_id
  JOIN recipes r ON r.id=v.recipe_id
  WHERE p.recipe_version_id=v.id AND (i.basis!='EP_RAW_G' OR p.method!=r.cooking_method OR (
   p.ingredient_id!=i.ingredient_id AND NOT EXISTS (
    SELECT 1 FROM recipe_variant_rules vr WHERE vr.recipe_version_id=v.id
    AND vr.requirement_id=i.id AND vr.replacement_ingredient_id=p.ingredient_id)
  ))
 ) THEN
  RAISE EXCEPTION 'Transformation requires authored raw binding and Recipe method' USING ERRCODE='23514';
 END IF;
 IF v.review_status='REVIEWED' AND (
  EXISTS (SELECT 1 FROM recipe_variant_rules WHERE recipe_version_id=v.id AND source_kind='IMPORTED_DRAFT')
  OR EXISTS (SELECT 1 FROM recipe_rule_combinations WHERE recipe_version_id=v.id AND source_kind='IMPORTED_DRAFT')
  OR EXISTS (SELECT 1 FROM preparation_transformations WHERE recipe_version_id=v.id AND source_kind='IMPORTED_DRAFT')
 ) THEN
  RAISE EXCEPTION 'Imported draft child cannot masquerade as reviewed authorship' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
"""


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.execute(TRIGGERS)
    op.execute(
        "CREATE TRIGGER recipe_version_assembly BEFORE INSERT ON recipe_versions FOR EACH ROW EXECUTE FUNCTION menuto_recipe_begin_version()"
    )
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION menuto_recipe_immutable()"
        )
        op.execute(
            f"CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION menuto_recipe_immutable()"
        )
    for table in TABLES[2:-1]:
        op.execute(
            f"CREATE TRIGGER {table}_sealed_insert BEFORE INSERT ON {table} FOR EACH ROW EXECUTE FUNCTION menuto_recipe_child_insert()"
        )
    op.execute(
        "CREATE TRIGGER recipe_version_seal_check BEFORE INSERT ON recipe_version_seals FOR EACH ROW EXECUTE FUNCTION menuto_recipe_seal()"
    )


def downgrade():
    op.execute("LOCK TABLE " + ", ".join(TABLES) + " IN ACCESS EXCLUSIVE MODE")
    for table in TABLES:
        op.execute(
            "DO $$ BEGIN IF EXISTS (SELECT 1 FROM "
            + table
            + ") THEN RAISE EXCEPTION '0005 downgrade would lose Recipe facts/provenance; archive explicitly first' USING ERRCODE='23514'; END IF; END $$"
        )
    op.execute("ALTER TABLE recipe_versions DROP CONSTRAINT fk_recipe_version_required_seal")
    for table in reversed(TABLES):
        op.drop_table(table)
    op.execute(
        "DROP FUNCTION menuto_recipe_seal(); DROP FUNCTION menuto_recipe_child_insert(); DROP FUNCTION menuto_recipe_immutable(); DROP FUNCTION menuto_recipe_begin_version()"
    )
