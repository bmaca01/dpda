"""
Graph Builder module for DPDA visualization.
Generates graph representations in various formats for visualization libraries.
"""

from typing import Dict, Any, List, Set, Optional

from models.dpda_definition import DPDADefinition
from models.transition import Transition


class GraphBuilder:
    """Builder for DPDA graph visualizations."""

    def build_graph(self, dpda: DPDADefinition) -> Dict[str, Any]:
        """
        Build a generic graph representation of the DPDA.

        Args:
            dpda: The DPDA definition to visualize

        Returns:
            Dictionary with nodes and edges
        """
        nodes = []
        edges = []

        # Create nodes for each state
        for state in sorted(dpda.states):
            node = {
                'id': state,
                'label': state,
                'is_initial': state == dpda.initial_state,
                'is_accept': state in dpda.accept_states,
                'group': self._get_node_group(
                    state, dpda.initial_state, dpda.accept_states
                )
            }
            nodes.append(node)

        # Create edges for transitions
        for trans in dpda.transitions:
            edge = {
                'from': trans.from_state,
                'to': trans.to_state,
                'label': self._format_transition_label(trans),
                'is_epsilon': trans.input_symbol is None,
                'is_self_loop': trans.from_state == trans.to_state
            }
            edges.append(edge)

        return {'nodes': nodes, 'edges': edges}

    def _get_node_group(self, state: str, initial: str, accepts: Set[str]) -> str:
        """Get the styling group for a node."""
        if state == initial:
            return 'initial'
        elif state in accepts:
            return 'accept'
        else:
            return 'normal'

    def _format_transition_label(self, trans: Transition) -> str:
        """Format a transition into a readable label."""
        input_str = 'ε' if trans.input_symbol is None else trans.input_symbol
        stack_pop = 'ε' if trans.stack_top is None else trans.stack_top
        stack_push = 'ε' if trans.stack_push == '' else trans.stack_push

        return f"{input_str},{stack_pop}→{stack_push}"

    def to_dot(self, dpda: DPDADefinition) -> str:
        """
        Generate DOT format string for Graphviz visualization.

        Args:
            dpda: The DPDA definition to visualize

        Returns:
            DOT format string
        """
        lines = []
        lines.append("digraph DPDA {")
        lines.append("    rankdir=LR;")  # Left-to-right layout
        lines.append("    node [shape=circle];")
        lines.append("")

        # Add invisible start node for initial state arrow
        lines.append("    start [shape=none,label=\"\"];")
        lines.append(f"    start -> {dpda.initial_state};")
        lines.append("")

        # Define nodes
        for state in sorted(dpda.states):
            attributes = []

            if state in dpda.accept_states:
                attributes.append("shape=doublecircle")

            if attributes:
                lines.append(f"    {state} [{','.join(attributes)}];")
            else:
                lines.append(f"    {state};")

        lines.append("")

        # Define edges
        # Group transitions by (from, to) pairs
        edge_labels = {}
        for trans in dpda.transitions:
            key = (trans.from_state, trans.to_state)
            label = self._format_transition_label(trans)

            if key not in edge_labels:
                edge_labels[key] = []
            edge_labels[key].append(label)

        # Create edges with combined labels
        for (from_state, to_state), labels in edge_labels.items():
            combined_label = "\\n".join(labels)  # Newline between multiple transitions
            lines.append(f"    {from_state} -> {to_state} [label=\"{combined_label}\"];")

        lines.append("}")

        return "\n".join(lines)

    def to_d3(self, dpda: DPDADefinition) -> Dict[str, Any]:
        """
        Generate D3.js compatible data format.

        Args:
            dpda: The DPDA definition to visualize

        Returns:
            Dictionary with D3.js visualization data (nodes and links)
        """
        graph = self.build_graph(dpda)

        # Transform to D3 format
        d3_data = {
            'nodes': [],
            'links': []  # D3 uses 'links' instead of 'edges'
        }

        # Transform nodes
        for node in graph['nodes']:
            d3_node = {
                'id': node['id'],
                'group': node['group']  # Used for styling
            }
            d3_data['nodes'].append(d3_node)

        # Transform edges to links
        for edge in graph['edges']:
            d3_link = {
                'source': edge['from'],
                'target': edge['to'],
                'label': edge['label']
            }
            d3_data['links'].append(d3_link)

        return d3_data

    def to_cytoscape(self, dpda: DPDADefinition) -> Dict[str, Any]:
        """
        Generate Cytoscape.js compatible format.

        Args:
            dpda: The DPDA definition to visualize

        Returns:
            Dictionary with 'elements' key containing list of Cytoscape elements
        """
        elements = []

        # Add nodes
        for state in sorted(dpda.states):
            node_data = {
                'data': {
                    'id': state,
                    'label': state
                }
            }

            # Add classes for styling
            classes = []
            if state == dpda.initial_state:
                classes.append('initial')
            if state in dpda.accept_states:
                classes.append('accept')

            if classes:
                node_data['classes'] = ' '.join(classes)

            elements.append(node_data)

        # Add edges
        # Group transitions by (from, to) pairs for cleaner visualization
        edge_groups = {}
        for trans in dpda.transitions:
            key = (trans.from_state, trans.to_state)
            if key not in edge_groups:
                edge_groups[key] = []
            edge_groups[key].append(self._format_transition_label(trans))

        # Create edges with combined labels
        edge_id = 0
        for (from_state, to_state), labels in edge_groups.items():
            edge_data = {
                'data': {
                    'id': f'e{edge_id}',
                    'source': from_state,
                    'target': to_state,
                    'label': '\n'.join(labels)  # Multiple transitions on separate lines
                }
            }

            # Add class for self-loops
            if from_state == to_state:
                edge_data['classes'] = 'self-loop'

            elements.append(edge_data)
            edge_id += 1

        return {'elements': elements}