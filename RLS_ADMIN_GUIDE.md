# RLS Admin Quick Reference

Visual guide for managing Row-Level Security through Django admin.

## 📋 Quick Access

1. **Login to Django Admin**: `/admin/`
2. **RLS Management Section**:
   - **RLS Policies**: Configure individual security policies
   - **RLS Table Configurations**: Configure table-level RLS settings

## 🎯 Common Tasks

### Task 1: Enable RLS on a Table

**Path**: Admin → RLS Table Configurations → Add

```
┌─────────────────────────────────────────────┐
│ Add RLS Table Configuration                │
├─────────────────────────────────────────────┤
│ Table name: employee_employee               │
│ Description: Employee data access control   │
│                                             │
│ ✅ RLS enabled                              │
│ ☐ Force RLS (apply to table owner)         │
│                                             │
│ Session Variables:                          │
│ ✅ Use user_id                              │
│ ✅ Use scopes                               │
│ ✅ Use roles                                │
│ Custom session vars: {}                     │
│                                             │
│ [Save and continue editing] [Save] [Cancel]│
└─────────────────────────────────────────────┘
```

**Then apply**:
1. Go to: RLS Table Configurations
2. Select: ☑️ employee_employee
3. Action: **Enable RLS on selected tables**
4. Click: **Go**

### Task 2: Create and Apply a Policy

**Path**: Admin → RLS Policies → Add

```
┌─────────────────────────────────────────────┐
│ Add RLS Policy                              │
├─────────────────────────────────────────────┤
│ Name: employee_read_access                  │
│ Table name: employee_employee               │
│ Description: Allow users with Employee.Read │
│              scope to read employee data    │
│                                             │
│ Policy command: SELECT ▼                    │
│ Policy type: PERMISSIVE ▼                   │
│                                             │
│ Required scopes:                            │
│ [Search and select: Employee.Read]          │
│ Scope requirement: any ▼                    │
│                                             │
│ ✅ Is active                                │
│                                             │
│ [Save and continue editing] [Save] [Cancel]│
└─────────────────────────────────────────────┘
```

**Then apply**:
1. Go to: RLS Policies
2. Select: ☑️ employee_read_access
3. Action: **Apply selected policies to database**
4. Click: **Go**
5. See success message: ✅ "Successfully applied 1 RLS policies to database."

### Task 3: Check Policy Status

**Path**: Admin → RLS Policies

```
1. Select policies: ☑️ employee_read_access
2. Action: Check status of selected policies ▼
3. Click: Go

Result message:
┌─────────────────────────────────────────────┐
│ ✅ employee_read_access: ✓ Applied          │
│    RLS: ✓ Enabled                           │
└─────────────────────────────────────────────┘
```

### Task 4: Preview SQL Before Applying

**Path**: Admin → RLS Policies

```
1. Select policies: ☑️ employee_read_access
2. Action: Preview SQL for selected policies ▼
3. Click: Go

Preview shows:
┌─────────────────────────────────────────────┐
│ employee_read_access (employee_employee)    │
│                                             │
│ CREATE POLICY employee_read_access          │
│ ON employee_employee                        │
│ AS PERMISSIVE                               │
│ FOR SELECT                                  │
│ TO PUBLIC                                   │
│ USING (                                     │
│   current_setting('app.user_scopes', true)  │
│   ~* 'Employee.Read'                        │
│ );                                          │
└─────────────────────────────────────────────┘
```

## 🔧 Admin Actions Reference

### RLS Policies Admin

| Action | What It Does | When to Use |
|--------|--------------|-------------|
| **Apply selected policies to database** | Creates or updates policies in PostgreSQL | After creating/editing policies |
| **Remove selected policies from database** | Drops policies from PostgreSQL | When removing policies |
| **Preview SQL for selected policies** | Shows SQL without executing | Before applying to verify |
| **Check status of selected policies** | Verifies if policies exist in DB | To confirm policies are active |
| **Apply all policies for selected tables** | Applies all policies for selected tables' tables | Bulk apply for a table |

### RLS Table Configurations Admin

| Action | What It Does | When to Use |
|--------|--------------|-------------|
| **Enable RLS on selected tables** | Enables RLS in PostgreSQL | First time setup |
| **Disable RLS on selected tables** | Disables RLS in PostgreSQL | Temporarily turn off RLS |
| **Apply all policies for selected tables** | Applies all active policies for tables | After creating multiple policies |
| **Remove all policies for selected tables** | Drops all policies from tables | Clean up / reset |
| **Check RLS status for selected tables** | Shows RLS status and policy count | Verify configuration |

## 📊 Admin List Views

### RLS Policies List

```
┌────────────────────────────────────────────────────────────────┐
│ RLS Policies                                   [Add RLS Policy] │
├────────────────────────────────────────────────────────────────┤
│ Action: Apply selected policies to database ▼        [Go]      │
│                                                                 │
│ ☐ Name            │ Table     │ Command │ Scopes │ Status      │
│ ──────────────────┼───────────┼─────────┼────────┼─────────    │
│ ☐ employee_read   │ employee_ │ SELECT  │ 1(ANY) │ ✓ Active    │
│ ☐ employee_modify │ employee_ │ UPDATE  │ 1(ALL) │ ✓ Active    │
│ ☐ dept_access     │ departmen │ ALL     │ 2(ANY) │ ✗ Inactive  │
└────────────────────────────────────────────────────────────────┘

Filters:
• Is Active: All / Yes / No
• Policy Command: All / SELECT / INSERT / UPDATE / DELETE / ALL
• Policy Type: All / PERMISSIVE / RESTRICTIVE
• Table Name: All / employee_employee / department_department
```

### RLS Table Configurations List

```
┌────────────────────────────────────────────────────────────────┐
│ RLS Table Configurations         [Add RLS Table Configuration] │
├────────────────────────────────────────────────────────────────┤
│ Action: Apply all policies for selected tables ▼      [Go]     │
│                                                                 │
│ ☐ Table Name      │ RLS Status    │ Policies │ Session Vars   │
│ ──────────────────┼───────────────┼──────────┼──────────────   │
│ ☐ employee_       │ ✓ Enabled     │ 2 policy │ user_id,scopes │
│ ☐ department_     │ ✗ Disabled    │ 1 policy │ user_id,roles  │
└────────────────────────────────────────────────────────────────┘

Filters:
• RLS Enabled: All / Yes / No
• Force RLS: All / Yes / No
```

## 🎬 Step-by-Step Workflow

### Scenario: Secure Employee Data by Department

**Goal**: Users can only see employees in their own department

#### Step 1: Create Scope Definition (if not exists)

```
Admin → Scope Definitions → Add
Name: Employee.Read
Category: Employee
✅ Is active
[Save]
```

#### Step 2: Configure Table

```
Admin → RLS Table Configurations → Add
Table name: employee_employee
✅ RLS enabled
✅ Use user_id
✅ Use scopes
Custom session vars: {"app.user_department_id": "user.department.id"}
[Save]
```

#### Step 3: Create Policy

```
Admin → RLS Policies → Add
Name: employee_department_access
Table: employee_employee
Command: SELECT
Required scopes: Employee.Read
Custom USING expression:
  current_setting('app.user_scopes', true) ~* 'Employee.Read'
  AND department_id = current_setting('app.user_department_id', true)::int
✅ Is active
[Save]
```

#### Step 4: Apply Configuration

```
Method A (Individual):
  RLS Policies → ☑️ employee_department_access
  Action: Apply selected policies to database
  [Go]

Method B (Bulk):
  RLS Table Configurations → ☑️ employee_employee
  Action: Apply all policies for selected tables
  [Go]
```

#### Step 5: Verify

```
RLS Table Configurations → ☑️ employee_employee
Action: Check RLS status for selected tables
[Go]

Expected result:
✅ employee_employee: RLS ✓ Enabled | Policies: 1 in DB, 1 in Django
```

## 🔍 Troubleshooting via Admin

### Problem: Policy not working

**Check 1**: Is policy active?
- Go to RLS Policies
- Look at "Status" column
- Should show: ✓ Active

**Check 2**: Is policy in database?
- Select policy
- Action: Check status of selected policies
- Should show: ✓ Applied

**Check 3**: Is RLS enabled on table?
- Go to RLS Table Configurations
- Look at "RLS Status" column
- Should show: ✓ Enabled

**Fix**: Apply the policy
- Select policy
- Action: Apply selected policies to database
- Click Go

### Problem: Policy exists but wrong SQL

**Solution**: Update and reapply
1. Edit policy in admin
2. Change USING expression or scopes
3. Save
4. Select policy
5. Action: Apply selected policies to database (drops old, creates new)

### Problem: Need to start over

**Solution**: Remove all and reapply
1. Go to RLS Table Configurations
2. Select table
3. Action: Remove all policies for selected tables
4. Click Go
5. Then: Apply all policies for selected tables

## 💡 Pro Tips

### Tip 1: Preview Before Apply
Always preview SQL first when creating complex policies:
1. Save policy
2. Select policy
3. Action: Preview SQL
4. Review the SQL
5. If correct: Apply selected policies

### Tip 2: Use Bulk Actions
When setting up multiple tables:
1. Create all table configs
2. Create all policies
3. Select all tables in RLS Table Configurations
4. Action: Apply all policies for selected tables (applies everything at once)

### Tip 3: Check Status Regularly
After making changes:
- RLS Policies → Select all → Check status
- RLS Table Configurations → Select all → Check RLS status

### Tip 4: Use Filters
When working with many policies:
- Filter by Table Name to see policies for specific table
- Filter by Is Active to see only active policies
- Filter by Policy Command to see all SELECT policies

## 🎓 Example: Complete Setup via Admin

### Multi-Tenant SaaS Application

**Requirement**: Users only see data for their tenant

**Steps**:

1. **Create scope** (Admin → Scope Definitions):
   - Name: `Tenant.Read`
   - Save

2. **Configure table** (Admin → RLS Table Configurations):
   - Table: `saas_customer`
   - RLS enabled: ✅
   - Use scopes: ✅
   - Save

3. **Create policy** (Admin → RLS Policies):
   - Name: `tenant_isolation`
   - Table: `saas_customer`
   - Command: `ALL`
   - Required scopes: `Tenant.Read`
   - Custom USING: `tenant_id = current_setting('app.tenant_id', true)::uuid`
   - Active: ✅
   - Save

4. **Apply** (RLS Table Configurations):
   - Select: ☑️ `saas_customer`
   - Action: Apply all policies for selected tables
   - Go

5. **Verify** (RLS Table Configurations):
   - Select: ☑️ `saas_customer`
   - Action: Check RLS status
   - Expected: ✅ RLS ✓ Enabled | Policies: 1 in DB, 1 in Django

**Done!** No command line needed. All via Django admin.

## 📚 Related Documentation

- [Full RLS Guide](RLS_GUIDE.md) - Complete RLS documentation
- [Dynamic Permissions](DYNAMIC_PERMISSIONS.md) - Scope/role management
- [Database Config Guide](DATABASE_CONFIG_GUIDE.md) - Azure AD config

## 🆘 Need Help?

**Can't find RLS in admin?**
- Check INSTALLED_APPS includes `hub_auth_client.django`
- Run migrations: `python manage.py migrate`
- Check you're using PostgreSQL

**Actions not showing?**
- RLS requires PostgreSQL
- Check database ENGINE setting

**Policies not applying?**
- Check error messages in admin
- Verify table exists in database
- Check PostgreSQL permissions
