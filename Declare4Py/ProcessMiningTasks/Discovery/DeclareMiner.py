from __future__ import annotations

from abc import ABC

from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessMiningTasks.AbstractDiscovery import AbstractDiscovery
from Declare4Py.ProcessModels.DeclareModel import DeclareModel, DeclareModelTemplate
from Declare4Py.Utils.Declare.Checkers import ConstraintChecker




"""
Provides basic discovery functionalities

Parameters
--------
    Discovery
        inherit class init

Attributes
--------
    super()
        inheriting from class Discovery
    output_path : str
        if specified, save the discovered constraints in a DECLARE model to the provided path.

"""


class DeclareMiner(AbstractDiscovery, ABC):

    def __init__(self, log: D4PyEventLog, consider_vacuity: bool, min_support: float, itemsets_support: float = 0.9,
                 max_declare_cardinality: int = 1):
        super().__init__(log, DeclareModel(), min_support)
        self.consider_vacuity: bool = consider_vacuity
        self.itemsets_support: float = itemsets_support
        self.max_declare_cardinality: int = max_declare_cardinality

    def run(self) -> DeclareModel:
        """
        Performs discovery of the supported DECLARE templates for the provided log by using the computed frequent item
        sets.

        Parameters
        ----------
        consider_vacuity : bool
            True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

        max_declare_cardinality : int, optional
            the maximum cardinality that the algorithm checks for DECLARE templates supporting it (default 3).

        output_path : str, optional
            if specified, save the discovered constraints in a DECLARE model to the provided path.

        Returns
        -------
        basic_discovery_results
            dictionary containing the results indexed by discovered constraints. The value is a dictionary with keys
            the tuples containing id and name of traces that satisfy the constraint. The values of this inner dictionary
            is a CheckerResult object containing the number of pendings, activations, violations, fulfilments.
        """
        print("Computing discovery ...")
        if self.event_log is None:
            raise RuntimeError("You must load a log before.")
        if self.max_declare_cardinality <= 0:
            raise RuntimeError("Cardinality must be greater than 0.")

        frequent_item_sets = self.event_log.compute_frequent_itemsets(min_support=self.itemsets_support,
                                                                      case_id_col=self.event_log.get_case_name(),
                                                                      categorical_attributes=[self.event_log.get_concept_name()],
                                                                      algorithm='fpgrowth', remove_column_prefix=True)

        tpm_activities = self.event_log.get_event_attribute_values(self.event_log.get_concept_name())
        if not isinstance(tpm_activities, list):
            self.process_model.activities = tpm_activities.keys()

        for item_set in frequent_item_sets['itemsets']:
            length = len(item_set)
            if length == 1:
                for template in DeclareModelTemplate.get_unary_templates():
                    constraint = {"template": template, "activities": list(item_set), "condition": ("", "")}

                    if not template.supports_cardinality:
                        constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                       self.event_log,
                                                                                                       self.consider_vacuity,
                                                                                                       self.min_support)

                        if constraint_satisfaction:
                            self.process_model.constraints.append(constraint.copy())
                    else:
                        for i in range(self.max_declare_cardinality):
                            constraint['n'] = i + 1
                            constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                           self.event_log,
                                                                                                           self.consider_vacuity,
                                                                                                           self.min_support)
                            if constraint_satisfaction:
                                self.process_model.constraints.append(constraint.copy())

            elif length == 2:
                for template in DeclareModelTemplate.get_binary_not_shortcut_templates():
                    
                    constraint = {"template": template, "activities": list(item_set), "condition": ("", "")}

                    constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                   self.event_log,
                                                                                                   self.consider_vacuity,
                                                                                                   self.min_support)
                    if constraint_satisfaction:
                        self.process_model.constraints.append(constraint.copy())

                    constraint['activities'] = list(reversed(list(item_set)))

                    constraint_satisfaction = ConstraintChecker().constraint_checking_with_support(constraint,
                                                                                                   self.event_log,
                                                                                                   self.consider_vacuity,
                                                                                                   self.min_support)
                    if constraint_satisfaction:
                        self.process_model.constraints.append(constraint.copy())
        self.process_model.set_constraints()
        return self.process_model
