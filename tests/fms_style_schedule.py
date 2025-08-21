import jax.numpy as jnp
import optax
import matplotlib.pyplot as plt

# Define schedule parameters
total_steps = 12000
warmup_steps = 2000
lr = 3e-4
final_lr_ratio = 0.1  # cosine final LR = lr * final_lr_ratio

# Define warmup and cosine schedules
warmup = optax.polynomial_schedule(
    init_value=0.0,
    end_value=lr,
    power=2.0,
    transition_steps=warmup_steps
)

cosine = optax.cosine_decay_schedule(
    init_value=lr,
    decay_steps=total_steps,
    alpha=final_lr_ratio
)

# Define FMS-style schedule: min(warmup, cosine)
def fms_style_lr(step):
    return jnp.minimum(warmup(step), cosine(step))

def parse_fms_loss(fpath):
    stats = {'completed step': [], 'loss': [], 'lr': []}
    
    with open(fpath, 'r') as f:
        for l in f.readlines():
            if l.startswith('step:'):
                stats['completed step'].append(int(l.split(': ')[1]))
            elif l.startswith('loss:'):
                stats['loss'].append(float(l.split(': ')[1]))
            elif l.startswith('LR:'):
                stats['lr'].append(float(l.split(': ')[1]))

    return stats

# Print LR for each step
for step in range(total_steps + 1):
    print(f"Step {step:5d} | MaxText LR = {fms_style_lr(step):.8f}")