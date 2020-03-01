import spacy
from spacy.tokens import Span

from cycontext import ConTextComponent
from cycontext import ConTextItem

import pytest



nlp = spacy.load("en_core_web_sm")

class TestConTextComponent:

    def test_initiate(self):
        assert ConTextComponent(nlp)

    def test_default_patterns(self):
        """Test that default rules are loaded"""
        context = ConTextComponent(nlp)
        assert context.item_data

    def test_empty_patterns(self):
        """Test that no rules are loaded"""
        context = ConTextComponent(nlp, rules=None)
        assert not context.item_data

    def test_custom_patterns_json(self):
        """Test that rules are loaded from a json"""
        context = ConTextComponent(nlp, rules='other', rule_list='./kb/default_rules.json')
        assert context.item_data

    def test_custom_patterns_list(self):
        """Test that rules are loaded from a list"""
        item = ConTextItem("evidence of", "DEFINITE_EXISTENCE", "forward")
        context = ConTextComponent(nlp, rules='other', rule_list=[item])
        assert context.item_data

    def test_bad_rules_arg(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules='not valid')

    def test_bad_rule_list_path(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules='other', rule_list='not a path')

    def test_bad_rule_list_empty(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules='other', rule_list=[])

    def test_bad_rule_list_items(self):
        with pytest.raises(ValueError):
            ConTextComponent(nlp, rules='other', rule_list=["list of strings"])

    def test_call(self):
        doc = nlp("Pulmonary embolism has been ruled out.")
        context = ConTextComponent(nlp)
        doc = context(doc)
        assert isinstance(doc, spacy.tokens.doc.Doc)

    def test_registers_attributes(self):
        """Test that the default ConText attributes are set on ."""
        doc = nlp("There is consolidation.")
        doc.ents = (doc[-2:-1], )
        context = ConTextComponent(nlp)
        doc = context(doc)
        assert hasattr(doc._, "context_graph")
        assert hasattr(doc.ents[0]._, "modifiers")

    def test_registers_context_attributes(self):
        """Test that the additional attributes such as
        'is_negated' are registered on spaCy spans.
        """
        doc = nlp("This is a span.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        context(doc)
        span = doc[-2:]
        for attr_name in ["is_negated", "is_uncertain", "is_historical", "is_hypothetical", "is_family"]:
            assert hasattr(span._, attr_name)

    def test_default_attribute_values(self):
        """Check that default Span attributes have False values without any modifiers."""
        doc = nlp("There is evidence of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        doc.ents = (doc[-2:-1],)
        context(doc)
        for attr_name in ["is_negated", "is_uncertain", "is_historical", "is_hypothetical", "is_family"]:
            assert getattr(doc.ents[0]._, attr_name) is False

    def test_default_rules_match(self):
        context = ConTextComponent(nlp)
        matcher = context.matcher
        assert matcher(nlp("no evidence of"))

    def test_custom_rules_match(self):
        item = ConTextItem("no evidence of", "NEGATED_EXISTENCE", "forward")
        context = ConTextComponent(nlp, rules='other', rule_list=[item])
        matcher = context.phrase_matcher
        assert matcher(nlp("no evidence of"))


    def test_is_negated(self):
        doc = nlp("There is no evidence of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("no evidence of", "NEGATED_EXISTENCE", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_negated is True

    def test_is_historical(self):
        doc = nlp("History of pneumonia.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("history of", "HISTORICAL", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_historical is True

    def test_is_family(self):
        doc = nlp("Family history of breast cancer.")
        context = ConTextComponent(nlp, add_attrs=True, rules=None)
        item_data = [ConTextItem("family history of", "FAMILY", rule="forward")]
        context.add(item_data)
        doc.ents = (doc[-3:-1],)
        context(doc)

        assert doc.ents[0]._.is_family is True

    def test_custom_attribute_error(self):
        """Test that a custom spacy attribute which has not been set
        will throw a ValueError.
        """
        custom_attrs = {'FAKE_MODIFIER': {'non_existent_attribute': True},
                        }
        with pytest.raises(ValueError):
            ConTextComponent(nlp, add_attrs=custom_attrs)

    def test_custom_attributes_mapping(self):
        custom_attrs = {'NEGATED_EXISTENCE': {'is_negated': True},
                        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        assert context.context_attributes_mapping == custom_attrs

    def test_custom_attributes_value1(self):
        custom_attrs = {'NEGATED_EXISTENCE': {'is_negated': True},
                        }
        try:
            Span.set_extension("is_negated", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        context.add([ConTextItem("no evidence of", "NEGATED_EXISTENCE", "FORWARD")])
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_negated is True

    def test_custom_attributes_value2(self):
        custom_attrs = {'FAMILY': {'is_family': True},
                        }
        try:
            Span.set_extension("is_family", default=False)
        except:
            pass
        context = ConTextComponent(nlp, add_attrs=custom_attrs)
        context.add([ConTextItem("no evidence of", "DEFINITE_NEGATED_EXISTENCE", "FORWARD")])
        doc = nlp("There is no evidence of pneumonia.")
        doc.ents = (doc[-2:-1],)
        context(doc)

        assert doc.ents[0]._.is_family is False
