"""
Tests for DPDA visualization module.
Following TDD - these tests are written before implementation.
"""

import pytest
import json
from typing import Dict, Any, List

# These imports will fail initially (TDD Red phase)
from visualization.graph_builder import GraphBuilder
from models.dpda_definition import DPDADefinition
from models.transition import Transition


class TestGraphBuilder:
    """Test DPDA graph visualization builder."""

    @pytest.fixture
    def simple_dpda(self):
        """Create a simple DPDA for visualization testing."""
        states = {'q0', 'q1', 'q2'}
        input_alphabet = {'0', '1'}
        stack_alphabet = {'Z', 'X'}
        accept_states = {'q2'}

        transitions = [
            Transition('q0', '0', 'Z', 'q0', 'X,Z'),
            Transition('q0', '0', 'X', 'q0', 'X,X'),
            Transition('q0', '1', 'X', 'q1', ''),
            Transition('q1', '1', 'X', 'q1', ''),
            Transition('q1', None, 'Z', 'q2', 'Z'),
        ]

        return DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

    @pytest.fixture
    def self_loop_dpda(self):
        """Create DPDA with self-loops for visualization testing."""
        states = {'q0', 'q1'}
        input_alphabet = {'a', 'b'}
        stack_alphabet = {'Z'}
        accept_states = {'q1'}

        transitions = [
            Transition('q0', 'a', 'Z', 'q0', 'Z'),  # Self-loop
            Transition('q0', 'b', 'Z', 'q1', 'Z'),
            Transition('q1', 'b', 'Z', 'q1', 'Z'),  # Another self-loop
        ]

        return DPDADefinition(
            states=states,
            input_alphabet=input_alphabet,
            stack_alphabet=stack_alphabet,
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=accept_states,
            transitions=transitions
        )

    def test_build_graph_structure(self, simple_dpda):
        """Test basic graph structure creation."""
        builder = GraphBuilder()
        graph = builder.build_graph(simple_dpda)

        assert 'nodes' in graph
        assert 'edges' in graph
        assert len(graph['nodes']) == 3  # q0, q1, q2
        assert len(graph['edges']) == 5  # 5 transitions

    def test_node_attributes(self, simple_dpda):
        """Test that nodes have proper attributes."""
        builder = GraphBuilder()
        graph = builder.build_graph(simple_dpda)

        nodes_by_id = {node['id']: node for node in graph['nodes']}

        # Check initial state
        assert nodes_by_id['q0']['is_initial'] == True
        assert nodes_by_id['q1']['is_initial'] == False

        # Check accept states
        assert nodes_by_id['q2']['is_accept'] == True
        assert nodes_by_id['q0']['is_accept'] == False
        assert nodes_by_id['q1']['is_accept'] == False

        # Check labels
        assert nodes_by_id['q0']['label'] == 'q0'
        assert nodes_by_id['q1']['label'] == 'q1'
        assert nodes_by_id['q2']['label'] == 'q2'

    def test_edge_attributes(self, simple_dpda):
        """Test that edges have proper attributes."""
        builder = GraphBuilder()
        graph = builder.build_graph(simple_dpda)

        edges = graph['edges']

        # Find specific edges
        epsilon_edge = next(e for e in edges if e['from'] == 'q1' and e['to'] == 'q2')
        normal_edge = next(e for e in edges if e['from'] == 'q0' and e['to'] == 'q0'
                          and '0' in e['label'])

        # Check epsilon edge
        assert 'ε' in epsilon_edge['label'] or 'eps' in epsilon_edge['label']
        assert epsilon_edge['is_epsilon'] == True

        # Check normal edge
        assert normal_edge['is_epsilon'] == False
        assert '0' in normal_edge['label']

    def test_self_loops(self, self_loop_dpda):
        """Test handling of self-loop edges."""
        builder = GraphBuilder()
        graph = builder.build_graph(self_loop_dpda)

        edges = graph['edges']
        self_loops = [e for e in edges if e['from'] == e['to']]

        assert len(self_loops) == 2  # q0->q0 and q1->q1
        for loop in self_loops:
            assert loop['is_self_loop'] == True

    def test_to_dot_format(self, simple_dpda):
        """Test DOT format generation for Graphviz."""
        builder = GraphBuilder()
        dot_string = builder.to_dot(simple_dpda)

        assert isinstance(dot_string, str)
        assert 'digraph' in dot_string
        assert 'rankdir=LR' in dot_string  # Left-to-right layout

        # Check nodes
        assert 'q0' in dot_string
        assert 'q1' in dot_string
        assert 'q2' in dot_string

        # Check initial state marker
        assert 'q0 [' in dot_string
        assert 'shape=circle' in dot_string or 'shape=doublecircle' in dot_string

        # Check accept state
        assert 'q2 [' in dot_string
        assert 'shape=doublecircle' in dot_string  # Accept states are double circles

        # Check edges
        assert 'q0 -> q0' in dot_string  # Self-loop
        assert 'q0 -> q1' in dot_string
        assert 'q1 -> q2' in dot_string

    def test_to_d3_json(self, simple_dpda):
        """Test D3.js compatible JSON format generation."""
        builder = GraphBuilder()
        d3_json = builder.to_d3_json(simple_dpda)

        assert isinstance(d3_json, str)
        d3_data = json.loads(d3_json)

        assert 'nodes' in d3_data
        assert 'links' in d3_data  # D3 uses 'links' instead of 'edges'

        # Check node structure for D3
        for node in d3_data['nodes']:
            assert 'id' in node
            assert 'group' in node  # Group for styling (initial/accept/normal)

        # Check link structure for D3
        for link in d3_data['links']:
            assert 'source' in link
            assert 'target' in link
            assert 'label' in link

    def test_to_cytoscape(self, simple_dpda):
        """Test Cytoscape.js compatible format generation."""
        builder = GraphBuilder()
        cyto_data = builder.to_cytoscape(simple_dpda)

        assert isinstance(cyto_data, list)

        # Separate nodes and edges
        nodes = [elem for elem in cyto_data if 'source' not in elem.get('data', {})]
        edges = [elem for elem in cyto_data if 'source' in elem.get('data', {})]

        assert len(nodes) == 3
        # Edges may be grouped - q0->q0 has 2 transitions combined
        assert len(edges) == 4  # Combined transitions reduce edge count

        # Check Cytoscape node format
        for node in nodes:
            assert 'data' in node
            assert 'id' in node['data']
            assert 'label' in node['data']

        # Check Cytoscape edge format
        for edge in edges:
            assert 'data' in edge
            assert 'source' in edge['data']
            assert 'target' in edge['data']
            assert 'label' in edge['data']

    def test_transition_label_formatting(self, simple_dpda):
        """Test that transition labels are properly formatted."""
        builder = GraphBuilder()
        graph = builder.build_graph(simple_dpda)

        # Check various label formats
        edges = graph['edges']

        # Normal transition: input,stack_top→stack_push
        normal_edge = next(e for e in edges if e['from'] == 'q0' and '0' in e['label'])
        assert '0,Z→X,Z' in normal_edge['label'] or '0,Z->X,Z' in normal_edge['label']

        # Pop transition
        pop_edge = next(e for e in edges if e['from'] == 'q0' and e['to'] == 'q1')
        assert '1,X→ε' in pop_edge['label'] or '1,X->eps' in pop_edge['label']

        # Epsilon transition
        eps_edge = next(e for e in edges if e['from'] == 'q1' and e['to'] == 'q2')
        assert 'ε,Z→Z' in eps_edge['label'] or 'eps,Z->Z' in eps_edge['label']

    def test_multiple_transitions_between_states(self):
        """Test handling of multiple transitions between same states."""
        states = {'q0', 'q1'}
        transitions = [
            Transition('q0', 'a', 'Z', 'q1', 'Z'),
            Transition('q0', 'b', 'Z', 'q1', 'Z'),
            Transition('q0', 'c', 'X', 'q1', 'X'),
        ]

        dpda = DPDADefinition(
            states=states,
            input_alphabet={'a', 'b', 'c'},
            stack_alphabet={'Z', 'X'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=set(),
            transitions=transitions
        )

        builder = GraphBuilder()
        graph = builder.build_graph(dpda)

        # Multiple transitions should be represented
        edges_q0_to_q1 = [e for e in graph['edges']
                          if e['from'] == 'q0' and e['to'] == 'q1']

        # Could be combined into one edge with multiple labels or separate edges
        assert len(edges_q0_to_q1) >= 1

        # Check all transitions are represented
        all_labels = ' '.join(e['label'] for e in edges_q0_to_q1)
        assert 'a,Z' in all_labels
        assert 'b,Z' in all_labels
        assert 'c,X' in all_labels

    def test_empty_dpda_visualization(self):
        """Test visualization of minimal DPDA."""
        dpda = DPDADefinition(
            states={'q0'},
            input_alphabet=set(),
            stack_alphabet={'Z'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states=set(),
            transitions=[]
        )

        builder = GraphBuilder()
        graph = builder.build_graph(dpda)

        assert len(graph['nodes']) == 1
        assert len(graph['edges']) == 0

        # Should still generate valid formats
        dot = builder.to_dot(dpda)
        assert 'digraph' in dot
        assert 'q0' in dot

    def test_node_styling_groups(self, simple_dpda):
        """Test that nodes are properly grouped for styling."""
        builder = GraphBuilder()
        graph = builder.build_graph(simple_dpda)

        nodes_by_id = {node['id']: node for node in graph['nodes']}

        # Check styling groups
        assert nodes_by_id['q0']['group'] == 'initial'
        assert nodes_by_id['q1']['group'] == 'normal'
        assert nodes_by_id['q2']['group'] == 'accept'

    def test_complex_stack_operations(self):
        """Test visualization of complex stack operations."""
        dpda = DPDADefinition(
            states={'q0', 'q1'},
            input_alphabet={'a'},
            stack_alphabet={'Z', 'A', 'B', 'C'},
            initial_state='q0',
            initial_stack_symbol='Z',
            accept_states={'q1'},
            transitions=[
                Transition('q0', 'a', 'Z', 'q0', 'A,B,C,Z'),  # Push multiple
                Transition('q0', None, 'A', 'q1', ''),  # Epsilon pop
            ]
        )

        builder = GraphBuilder()
        graph = builder.build_graph(dpda)

        edges = graph['edges']

        # Find the complex push transition
        complex_edge = next(e for e in edges
                           if e['from'] == 'q0' and e['to'] == 'q0')

        # Should show the full stack operation
        assert 'A,B,C,Z' in complex_edge['label']