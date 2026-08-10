# Reinforcement Learning Rules

- **Model architecture and naming**
  - For on-policy algorithms with high-dimensional inputs such as images,
    prefer sharing an expensive low-level feature extractor between the
    `Actor` and `VCritic`, while keeping their task-specific networks
    independent.
  - For on-policy algorithms with low-dimensional vector inputs, use
    independent `Actor` and `VCritic` MLPs with no shared parameters by
    default.
  - Define the `Actor` and `VCritic` as separate classes, including when they
    share a feature extractor.
  - For off-policy algorithms, use completely independent networks and
    parameters for the `Actor` and `QCritic`; do not share a backbone.
  - Name every policy network `Actor`, every state-value network `VCritic`,
    and every action-value network `QCritic`.
  - When an algorithm has multiple Q networks, use clear and consistent names
    such as `QCritic1` and `QCritic2`.

- **SKRL**
  - **Agent configuration**
    - For each SKRL agent, align parameters that have direct semantic
      equivalents with the defaults of the corresponding Stable-Baselines3
      (SB3) algorithm. This does not apply to parameters without an SB3
      equivalent.
  - **Training**
    - Keep the default total transition budget small enough for a quick
      feasibility check. Use a long training run only when requested.
  - **Logging**
    - Always enable at least one experiment tracking system in every training
      script.
    - Unless the user specifies otherwise, use Weights & Biases (W&B) when
      network access is available; use TensorBoard when offline or when local
      visualization or offline analysis is required.
    - Use the SKRL experiment configuration to set the experiment name, log
      directory, and write interval explicitly.
  - **Artifacts**
    - Choose a checkpoint interval that produces at least 20 checkpoints over
      the configured training budget.
    - Store experiment logs and checkpoints in a clear, stable directory
      structure.
  - **Transition accounting**
    - Express user-facing training progress, logging intervals, and checkpoint
      intervals as total transitions accumulated across all vector
      environments.
    - Keep rollout horizons in steps per environment because they represent
      the temporal span used for on-policy return and advantage estimation.
    - Prefix cumulative quantity names with `TOTAL_` and suffix
      per-environment quantity names with `_PER_ENV`.
    - Convert total quantities to the units expected by SKRL only at the SKRL
      API boundary.
    - Label logs and checkpoint files with the total number of transitions.
