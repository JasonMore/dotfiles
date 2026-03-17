# Projects API Recipes

## CLI Fast Path

```bash
gh project list --owner <owner> --format json
gh project view <number> --owner <owner> --format json
gh project field-list <number> --owner <owner> --format json
gh project item-list <number> --owner <owner> --limit 200 --format json
```

## GraphQL Node-ID Path

### Find project node ID
```bash
gh api graphql -f query='query($owner:String!,$number:Int!){organization(login:$owner){projectV2(number:$number){id}}}' -f owner=<org> -F number=<number>
```

### Add item by node ID
```bash
gh api graphql -f query='mutation($input:AddProjectV2ItemByIdInput!){addProjectV2ItemById(input:$input){item{id}}}' -f input='{"projectId":"PROJECT_NODE_ID","contentId":"CONTENT_NODE_ID"}'
```

### Update field value
```bash
gh api graphql -f query='mutation($input:UpdateProjectV2ItemFieldValueInput!){updateProjectV2ItemFieldValue(input:$input){projectV2Item{id}}}' -f input='{"projectId":"PROJECT_NODE_ID","itemId":"ITEM_NODE_ID","fieldId":"FIELD_NODE_ID","value":{"text":"updated"}}'
```

## REST Projects v2 Path

Include headers in full commands:

```bash
gh api /orgs/<org>/projectsV2 \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28"
```

Representative routes:
- `GET /orgs/{org}/projectsV2`
- `GET /orgs/{org}/projectsV2/{project_number}`
- `GET /orgs/{org}/projectsV2/{project_number}/fields`
- `GET /orgs/{org}/projectsV2/{project_number}/items`
- `POST /orgs/{org}/projectsV2/{project_number}/items`
- `POST /orgs/{org}/projectsV2/{project_number}/drafts`
- `POST /orgs/{org}/projectsV2/{project_number}/views`
