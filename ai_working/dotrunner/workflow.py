"""
Workflow and Node data models for DotRunner.

These dataclasses represent the core structure of workflow definitions
loaded from YAML files.
"""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Union

import yaml


@dataclass
class Node:
    """
    Single workflow node representing a task.

    A node is the atomic unit of work in a workflow. Each node:
    - Has a unique ID within the workflow
    - Defines a prompt to execute (with context interpolation)
    - Can specify which agent to use
    - Can produce named outputs for downstream nodes
    - Can route to next node(s) conditionally or unconditionally
    """

    id: str  # Unique node identifier
    name: str  # Human-readable name
    prompt: str  # Prompt template with {var} interpolation

    # Optional fields with defaults
    agent: str = "auto"  # Agent to use (or "auto" for generic)
    outputs: list[str] = field(default_factory=list)  # Named outputs to capture
    next: Union[str, list[dict]] | None = None  # Next node or conditions
    retry_on_failure: int = 1  # Number of retry attempts
    type: str | None = None  # "terminal" for end nodes


@dataclass
class Workflow:
    """
    Complete workflow definition with nodes and global context.

    A workflow is a directed graph of nodes that execute in sequence or
    based on conditional routing. It includes:
    - Metadata (name, description)
    - List of nodes to execute
    - Global context available to all nodes
    """

    name: str  # Workflow identifier
    description: str  # What this workflow does
    nodes: list[Node]  # Ordered list of nodes

    # Optional fields with defaults
    context: dict[str, Any] = field(default_factory=dict)  # Global context

    def get_node(self, node_id: str) -> Node | None:
        """
        Get node by ID.

        Args:
            node_id: Node identifier to find

        Returns:
            Node if found, None otherwise
        """
        return next((n for n in self.nodes if n.id == node_id), None)

    def validate(self) -> None:
        """
        Validate workflow structure and relationships.

        Raises:
            ValueError: If workflow is invalid

        Checks:
        - At least one node exists
        - All node IDs are unique
        - All node references point to valid nodes
        - No circular dependencies exist
        """
        # Check at least one node
        if not self.nodes:
            raise ValueError("Workflow must have at least one node")

        # Check for duplicate node IDs
        node_ids = [n.id for n in self.nodes]
        duplicates = [nid for nid in node_ids if node_ids.count(nid) > 1]
        if duplicates:
            raise ValueError(f"Duplicate node ID found: {duplicates[0]}")

        # Check all node references are valid
        for node in self.nodes:
            if isinstance(node.next, str):
                # Simple next reference
                if not self.get_node(node.next):
                    raise ValueError(f"Node '{node.id}' references nonexistent node '{node.next}'")
            elif isinstance(node.next, list):
                # Conditional next references
                for condition in node.next:
                    if "goto" in condition:
                        target = condition["goto"]
                        if not self.get_node(target):
                            raise ValueError(f"Node '{node.id}' condition references nonexistent node '{target}'")

        # Check for circular dependencies
        self._detect_cycles()

    def _detect_cycles(self) -> None:
        """
        Detect circular dependencies in workflow graph.

        Uses depth-first search to find cycles.

        Raises:
            ValueError: If circular dependency detected
        """
        # Track visited nodes and current path
        visited = set()
        rec_stack = set()

        def visit(node_id: str, path: list[str]) -> None:
            if node_id in rec_stack:
                cycle_path = " -> ".join(path + [node_id])
                raise ValueError(f"Circular dependency detected: {cycle_path}")

            if node_id in visited:
                return

            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.get_node(node_id)
            if node:
                # Get next node(s)
                next_nodes = []
                if isinstance(node.next, str):
                    next_nodes = [node.next]
                elif isinstance(node.next, list):
                    next_nodes = [c["goto"] for c in node.next if "goto" in c]

                # Visit each next node
                for next_id in next_nodes:
                    visit(next_id, path + [node_id])

            rec_stack.remove(node_id)

        # Start from each node (to catch disconnected components)
        for node in self.nodes:
            if node.id not in visited:
                visit(node.id, [])

    @classmethod
    def from_yaml(cls, path: Path) -> "Workflow":
        """
        Load workflow from YAML file.

        Args:
            path: Path to YAML workflow file

        Returns:
            Workflow instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")

        if not data:
            raise ValueError("Empty YAML file")

        if "workflow" not in data:
            raise ValueError("Missing required field: workflow")

        workflow_data = data["workflow"]

        # Validate required workflow fields
        for field_name in ["name", "description"]:
            if field_name not in workflow_data:
                raise ValueError(f"Missing required field: workflow.{field_name}")

        if "nodes" not in data:
            raise ValueError("Missing required field: nodes")

        # Parse nodes
        nodes_data = data["nodes"]
        if not isinstance(nodes_data, list):
            raise ValueError("nodes must be a list")

        nodes = []
        for node_data in nodes_data:
            # Validate required node fields
            for field_name in ["id", "name", "prompt"]:
                if field_name not in node_data:
                    raise ValueError(f"Missing required field in node: {field_name}")

            # Create node with all fields
            node = Node(
                id=node_data["id"],
                name=node_data["name"],
                prompt=node_data["prompt"],
                agent=node_data.get("agent", "auto"),
                outputs=node_data.get("outputs", []),
                next=node_data.get("next"),
                retry_on_failure=node_data.get("retry_on_failure", 1),
                type=node_data.get("type"),
            )
            nodes.append(node)

        # Create workflow
        workflow = cls(
            name=workflow_data["name"],
            description=workflow_data["description"],
            nodes=nodes,
            context=workflow_data.get("context", {}),
        )

        # Validate workflow structure
        workflow.validate()

        return workflow
