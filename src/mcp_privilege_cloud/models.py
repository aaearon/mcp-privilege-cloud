"""
Response Models for CyberArk MCP Server

Pydantic models for typed MCP tool returns with JSON schema generation.
Models use aliases to match CyberArk API field names (CamelCase) while
providing Pythonic snake_case attribute access.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AccountDetails(BaseModel):
    """Detailed account information from CyberArk Privilege Cloud."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"  # Allow extra fields for API forward compatibility
    )

    id: str = Field(description="Unique account identifier")
    platform_id: str = Field(alias="platformId", description="Platform identifier")
    safe_name: str = Field(alias="safeName", description="Safe name containing the account")
    name: Optional[str] = Field(default=None, description="Account display name")
    user_name: Optional[str] = Field(default=None, alias="userName", description="Account username")
    address: Optional[str] = Field(default=None, description="Target system address")
    secret_type: Optional[str] = Field(default=None, alias="secretType", description="Secret type (password, key)")
    created_time: Optional[str] = Field(default=None, alias="createdTime", description="Account creation timestamp")
    secret_management: Optional[Dict[str, Any]] = Field(
        default=None, alias="secretManagement", description="Secret management settings"
    )
    platform_account_properties: Optional[Dict[str, Any]] = Field(
        default=None, alias="platformAccountProperties", description="Platform-specific properties"
    )


class AccountSummary(BaseModel):
    """Summary account information for list operations."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    id: str = Field(description="Unique account identifier")
    name: Optional[str] = Field(default=None, description="Account display name")
    platform_id: str = Field(alias="platformId", description="Platform identifier")
    safe_name: str = Field(alias="safeName", description="Safe name")
    user_name: Optional[str] = Field(default=None, alias="userName", description="Account username")
    address: Optional[str] = Field(default=None, description="Target system address")


class AccountsList(BaseModel):
    """Paginated list of accounts."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    value: List[AccountSummary] = Field(description="List of accounts")
    count: int = Field(description="Total number of accounts")
    next_link: Optional[str] = Field(default=None, alias="nextLink", description="Next page URL")


class SafeCreator(BaseModel):
    """Safe creator information."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    id: Optional[str] = Field(default=None, description="Creator user ID")
    name: Optional[str] = Field(default=None, description="Creator name")


class SafeDetails(BaseModel):
    """Detailed safe information from CyberArk Privilege Cloud."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    safe_url_id: str = Field(alias="safeUrlId", description="URL-safe identifier")
    safe_name: str = Field(alias="safeName", description="Safe name")
    safe_number: Optional[int] = Field(default=None, alias="safeNumber", description="Safe number")
    description: Optional[str] = Field(default=None, description="Safe description")
    location: Optional[str] = Field(default=None, description="Safe location in vault")
    creator: Optional[SafeCreator] = Field(default=None, description="Safe creator information")
    olac_enabled: Optional[bool] = Field(default=None, alias="olacEnabled", description="Object level access control enabled")
    number_of_days_retention: Optional[int] = Field(
        default=None, alias="numberOfDaysRetention", description="Retention days"
    )
    number_of_versions_retention: Optional[int] = Field(
        default=None, alias="numberOfVersionsRetention", description="Retention versions"
    )
    auto_purge_enabled: Optional[bool] = Field(default=None, alias="autoPurgeEnabled", description="Auto purge enabled")
    managing_cpm: Optional[str] = Field(default=None, alias="managingCPM", description="Managing CPM name")


class SafeMemberPermissions(BaseModel):
    """Safe member permissions."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    use_accounts: Optional[bool] = Field(default=None, alias="useAccounts")
    retrieve_accounts: Optional[bool] = Field(default=None, alias="retrieveAccounts")
    list_accounts: Optional[bool] = Field(default=None, alias="listAccounts")
    add_accounts: Optional[bool] = Field(default=None, alias="addAccounts")
    update_account_content: Optional[bool] = Field(default=None, alias="updateAccountContent")
    update_account_properties: Optional[bool] = Field(default=None, alias="updateAccountProperties")
    rename_accounts: Optional[bool] = Field(default=None, alias="renameAccounts")
    delete_accounts: Optional[bool] = Field(default=None, alias="deleteAccounts")
    unlock_accounts: Optional[bool] = Field(default=None, alias="unlockAccounts")
    manage_safe: Optional[bool] = Field(default=None, alias="manageSafe")
    manage_safe_members: Optional[bool] = Field(default=None, alias="manageSafeMembers")
    view_audit_log: Optional[bool] = Field(default=None, alias="viewAuditLog")
    view_safe_members: Optional[bool] = Field(default=None, alias="viewSafeMembers")


class SafeMember(BaseModel):
    """Safe member with permissions."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    member_name: str = Field(alias="memberName", description="Member name/username")
    member_type: str = Field(alias="memberType", description="Member type (User, Group, Role)")
    membership_expiration_date: Optional[str] = Field(
        default=None, alias="membershipExpirationDate", description="Membership expiration date"
    )
    permissions: Optional[Dict[str, Any]] = Field(default=None, description="Member permissions")
    search_in: Optional[str] = Field(default=None, alias="searchIn", description="Domain to search in")


class PlatformDetails(BaseModel):
    """Platform configuration details from CyberArk Privilege Cloud."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"  # Allow Policy INI fields
    )

    id: str = Field(description="Platform identifier")
    name: str = Field(description="Platform display name")
    system_type: Optional[str] = Field(default=None, alias="systemType", description="System type (Windows, Unix, etc.)")
    active: Optional[bool] = Field(default=None, description="Whether platform is active")
    platform_type: Optional[str] = Field(default=None, alias="platformType", description="Platform type (Regular, Group, etc.)")
    description: Optional[str] = Field(default=None, description="Platform description")
    platform_base_id: Optional[str] = Field(default=None, alias="platformBaseID", description="Base platform ID")
    privileged_access_workflows: Optional[Dict[str, Any]] = Field(
        default=None, alias="privilegedAccessWorkflows", description="Privileged access workflow settings"
    )


class ApplicationDetails(BaseModel):
    """Application details from CyberArk Privilege Cloud."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    app_id: str = Field(alias="AppID", description="Application identifier")
    description: Optional[str] = Field(default=None, alias="Description", description="Application description")
    location: Optional[str] = Field(default=None, alias="Location", description="Application location")
    disabled: Optional[bool] = Field(default=None, alias="Disabled", description="Whether application is disabled")
    business_owner_first_name: Optional[str] = Field(
        default=None, alias="BusinessOwnerFName", description="Business owner first name"
    )
    business_owner_last_name: Optional[str] = Field(
        default=None, alias="BusinessOwnerLName", description="Business owner last name"
    )
    business_owner_email: Optional[str] = Field(
        default=None, alias="BusinessOwnerEmail", description="Business owner email"
    )
    business_owner_phone: Optional[str] = Field(
        default=None, alias="BusinessOwnerPhone", description="Business owner phone"
    )
    access_permitted_from: Optional[str] = Field(
        default=None, alias="AccessPermittedFrom", description="Access start time"
    )
    access_permitted_to: Optional[str] = Field(
        default=None, alias="AccessPermittedTo", description="Access end time"
    )
    expiration_date: Optional[str] = Field(
        default=None, alias="ExpirationDate", description="Application expiration date"
    )


class ApplicationAuthMethod(BaseModel):
    """Application authentication method."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    auth_type: str = Field(alias="authType", description="Authentication type")
    auth_value: Optional[str] = Field(default=None, alias="authValue", description="Authentication value")
    auth_id: Optional[str] = Field(default=None, alias="authID", description="Authentication method ID")
    is_folder: Optional[bool] = Field(default=None, alias="isFolder", description="Whether this is a folder auth")
    allow_internal_scripts: Optional[bool] = Field(
        default=None, alias="allowInternalScripts", description="Allow internal scripts"
    )
    comment: Optional[str] = Field(default=None, description="Authentication method comment")


class SessionDetails(BaseModel):
    """Privileged session details from CyberArk Session Monitoring."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    session_id: str = Field(alias="SessionId", description="Unique session identifier")
    protocol: Optional[str] = Field(default=None, alias="Protocol", description="Session protocol (SSH, RDP, etc.)")
    user: Optional[str] = Field(default=None, alias="User", description="User who initiated the session")
    from_ip: Optional[str] = Field(default=None, alias="FromIP", description="Source IP address")
    to_address: Optional[str] = Field(default=None, alias="ToAddress", description="Target address")
    to_user: Optional[str] = Field(default=None, alias="ToUser", description="Target user")
    session_duration: Optional[str] = Field(default=None, alias="SessionDuration", description="Session duration")
    start_time: Optional[str] = Field(default=None, alias="StartTime", description="Session start time")
    end_time: Optional[str] = Field(default=None, alias="EndTime", description="Session end time")
    risk_score: Optional[int] = Field(default=None, alias="RiskScore", description="Session risk score")


class SessionActivity(BaseModel):
    """Session activity log entry."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    timestamp: str = Field(alias="Timestamp", description="Activity timestamp")
    command: Optional[str] = Field(default=None, alias="Command", description="Command executed")
    result: Optional[str] = Field(default=None, alias="Result", description="Command result")
    activity_type: Optional[str] = Field(default=None, alias="ActivityType", description="Type of activity")


class SessionStatistics(BaseModel):
    """Session statistics and analytics."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    total_sessions: Optional[int] = Field(default=None, alias="totalSessions", description="Total session count")
    active_sessions: Optional[int] = Field(default=None, alias="activeSessions", description="Active session count")
    sessions_by_protocol: Optional[Dict[str, int]] = Field(
        default=None, alias="sessionsByProtocol", description="Sessions grouped by protocol"
    )


class OperationResponse(BaseModel):
    """Generic operation response for create/update/delete operations."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    success: bool = Field(description="Whether the operation succeeded")
    message: Optional[str] = Field(default=None, description="Operation result message")
    id: Optional[str] = Field(default=None, description="ID of affected resource")


class ErrorResponse(BaseModel):
    """Error response from CyberArk API."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow"
    )

    error_code: Optional[str] = Field(default=None, alias="ErrorCode", description="Error code")
    error_message: Optional[str] = Field(default=None, alias="ErrorMessage", description="Error message")
    details: Optional[str] = Field(default=None, alias="Details", description="Error details")
