# Azure Credentials and SSH Key Configuration

## IMPORTANT: GitHub Secrets Required

The following credentials have been provided and SHOULD BE ADDED GITHUB REPOSITORY SECRETS (not as files):

### Azure Credentials
Add these as repository secrets:

1. **AZURE_SUBSCRIPTION_ID**
   - Value: `672377f1-75ac-45aa-8648-4c915f62a058`

2. **AZURE_CLIENT_ID**
   - Value: `38df2ac1-0d73-4bc2-9681-efc9696299f5`

3. **AZURE_CLIENT_SECRET**
   - Value: `u_T8Q~OVhL4mLmh21KffHFTKsZnREkGLTtuiNaU~`

4. **AZURE_TENANT_ID**
   - Value: `ffa7d9d1-fac9-4290-81e2-1357c9d37865`

### How to Add GitHub Secrets:
1. Go to the repository on GitHub
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret" for each credential above
4. Enter the secret name and value

---

## SSH Key for VM Access

Generate an Ed25519 SSH key pair using:

```bash
ssh-keygen -t ed25519 -C "vm-access-key" -f ~/.ssh/id_ed25519
```

Add the generated **private key** (`id_ed25519` or whatever you named it) as a repository secret called:
- **SSH_PRIVATE_KEY**

**IMPORTANT**: Never commit actual private keys to git! Store them ONLY in GitHub Secrets.

To use in GitHub Actions:
```yaml
- name: Setup SSH
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
    chmod 600 ~/.ssh/id_ed25519
    ssh-keyscan github.com >> ~/.ssh/known_hosts
```

---

## Note on This File
This file only contains instructions. The actual credentials SHOULD NOT be stored as files - use GitHub Secrets instead.