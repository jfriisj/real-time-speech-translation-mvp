# Creating custom agents

You can create specialized agents with tailored expertise for specific development tasks.

Custom agents allow you to create specialized agents with tailored expertise for specific tasks. For a conceptual overview of custom agents, see [About custom agents](/en/copilot/concepts/agents/coding-agent/about-custom-agents).

> \[!NOTE]
> Custom agents are in public preview for JetBrains IDEs, Eclipse, and Xcode, and subject to change.

## Creating a custom agent profile in a repository on GitHub

1. Navigate to the agents tab at [https://github.com/copilot/agents](https://github.com/copilot/agents?ref_product=copilot\&ref_type=engagement\&ref_style=text).

2. Using the dropdown menu in the prompt box, select the repository you want to create the custom agent profile in.

   > \[!NOTE]
   > Organization and enterprise owners can create organization and enterprise-level custom agents in a `.github-private` repository that are available across all repositories within their organization or enterprise. For more information, see [Preparing to use custom agents in your enterprise](/en/copilot/how-tos/administer-copilot/manage-for-enterprise/manage-agents/prepare-for-custom-agents) and [Preparing to use custom agents in your organization](/en/copilot/how-tos/administer-copilot/manage-for-organization/prepare-for-custom-agents).

3. Optionally, select the branch you want to create the agent profile in. The default is the main branch.

4. Click <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-copilot" aria-label="Select a custom agent" role="img"><path d="M7.998 15.035c-4.562 0-7.873-2.914-7.998-3.749V9.338c.085-.628.677-1.686 1.588-2.065.013-.07.024-.143.036-.218.029-.183.06-.384.126-.612-.201-.508-.254-1.084-.254-1.656 0-.87.128-1.769.693-2.484.579-.733 1.494-1.124 2.724-1.261 1.206-.134 2.262.034 2.944.765.05.053.096.108.139.165.044-.057.094-.112.143-.165.682-.731 1.738-.899 2.944-.765 1.23.137 2.145.528 2.724 1.261.566.715.693 1.614.693 2.484 0 .572-.053 1.148-.254 1.656.066.228.098.429.126.612.012.076.024.148.037.218.924.385 1.522 1.471 1.591 2.095v1.872c0 .766-3.351 3.795-8.002 3.795Zm0-1.485c2.28 0 4.584-1.11 5.002-1.433V7.862l-.023-.116c-.49.21-1.075.291-1.727.291-1.146 0-2.059-.327-2.71-.991A3.222 3.222 0 0 1 8 6.303a3.24 3.24 0 0 1-.544.743c-.65.664-1.563.991-2.71.991-.652 0-1.236-.081-1.727-.291l-.023.116v4.255c.419.323 2.722 1.433 5.002 1.433ZM6.762 2.83c-.193-.206-.637-.413-1.682-.297-1.019.113-1.479.404-1.713.7-.247.312-.369.789-.369 1.554 0 .793.129 1.171.308 1.371.162.181.519.379 1.442.379.853 0 1.339-.235 1.638-.54.315-.322.527-.827.617-1.553.117-.935-.037-1.395-.241-1.614Zm4.155-.297c-1.044-.116-1.488.091-1.681.297-.204.219-.359.679-.242 1.614.091.726.303 1.231.618 1.553.299.305.784.54 1.638.54.922 0 1.28-.198 1.442-.379.179-.2.308-.578.308-1.371 0-.765-.123-1.242-.37-1.554-.233-.296-.693-.587-1.713-.7Z"></path><path d="M6.25 9.037a.75.75 0 0 1 .75.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 .75-.75Zm4.25.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 1.5 0Z"></path></svg>, then click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-plus" aria-label="Plus button" role="img"><path d="M7.75 2a.75.75 0 0 1 .75.75V7h4.25a.75.75 0 0 1 0 1.5H8.5v4.25a.75.75 0 0 1-1.5 0V8.5H2.75a.75.75 0 0 1 0-1.5H7V2.75A.75.75 0 0 1 7.75 2Z"></path></svg> Create an agent**. This will open a template agent profile called `my-agent.agent.md` in the `.github/agents` directory of your target repository.

5. If you are creating an organization or enterprise-level custom agent, delete the `.github/` portion of the file path to move your template to the root `agents` directory.

6. Edit the filename (the text before `.agent.md`), selecting a unique, descriptive name that identifies the agent's purpose. Note that the filename may only contain the following characters: `.`, `-`, `_`, `a-z`, `A-Z`, `0-9`.

7. Configure the agent profile, including the name, description, tools, and prompts. For more information on what the agent profile can include, see [Configuring an agent profile](#configuring-an-agent-profile).

8. Commit the file to the repository and merge it into the default branch. Go back to the agents tab and refresh the page if needed. Your custom agent will now appear in the dropdown when you click <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-copilot" aria-label="copilot" role="img"><path d="M7.998 15.035c-4.562 0-7.873-2.914-7.998-3.749V9.338c.085-.628.677-1.686 1.588-2.065.013-.07.024-.143.036-.218.029-.183.06-.384.126-.612-.201-.508-.254-1.084-.254-1.656 0-.87.128-1.769.693-2.484.579-.733 1.494-1.124 2.724-1.261 1.206-.134 2.262.034 2.944.765.05.053.096.108.139.165.044-.057.094-.112.143-.165.682-.731 1.738-.899 2.944-.765 1.23.137 2.145.528 2.724 1.261.566.715.693 1.614.693 2.484 0 .572-.053 1.148-.254 1.656.066.228.098.429.126.612.012.076.024.148.037.218.924.385 1.522 1.471 1.591 2.095v1.872c0 .766-3.351 3.795-8.002 3.795Zm0-1.485c2.28 0 4.584-1.11 5.002-1.433V7.862l-.023-.116c-.49.21-1.075.291-1.727.291-1.146 0-2.059-.327-2.71-.991A3.222 3.222 0 0 1 8 6.303a3.24 3.24 0 0 1-.544.743c-.65.664-1.563.991-2.71.991-.652 0-1.236-.081-1.727-.291l-.023.116v4.255c.419.323 2.722 1.433 5.002 1.433ZM6.762 2.83c-.193-.206-.637-.413-1.682-.297-1.019.113-1.479.404-1.713.7-.247.312-.369.789-.369 1.554 0 .793.129 1.171.308 1.371.162.181.519.379 1.442.379.853 0 1.339-.235 1.638-.54.315-.322.527-.827.617-1.553.117-.935-.037-1.395-.241-1.614Zm4.155-.297c-1.044-.116-1.488.091-1.681.297-.204.219-.359.679-.242 1.614.091.726.303 1.231.618 1.553.299.305.784.54 1.638.54.922 0 1.28-.198 1.442-.379.179-.2.308-.578.308-1.371 0-.765-.123-1.242-.37-1.554-.233-.296-.693-.587-1.713-.7Z"></path><path d="M6.25 9.037a.75.75 0 0 1 .75.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 .75-.75Zm4.25.75v1.501a.75.75 0 0 1-1.5 0V9.787a.75.75 0 0 1 1.5 0Z"></path></svg> in the prompt box.

## Creating a custom agent profile in Visual Studio Code

1. Open GitHub Copilot Chat in Visual Studio Code.
2. From the agents dropdown at the bottom of the chat view, click **Configure Custom Agents...**, then click **<svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-plus" aria-label="Plus button" role="img"><path d="M7.75 2a.75.75 0 0 1 .75.75V7h4.25a.75.75 0 0 1 0 1.5H8.5v4.25a.75.75 0 0 1-1.5 0V8.5H2.75a.75.75 0 0 1 0-1.5H7V2.75A.75.75 0 0 1 7.75 2Z"></path></svg> Create new custom agent**.
3. Choose the location where the agent profile should be created:
   * **Workspace**: Create the custom agent profile in the `.github/agents` folder of your workspace to only use it within that workspace.
   * **User profile**: Create the custom agent profile in the current user profile folder to use it across all your workspaces.
4. Enter a file name for the custom agent. This is the default name that appears in the agents dropdown.
5. Configure the agent profile in the newly created `.agent.md` file, including the description, tools, and prompts. For more information on what the agent profile can include, see [Configuring an agent profile](#configuring-an-agent-profile).
   * You can use the **Configure Tools...** button within the editor to open the "Configure Tools" dialog, where you can view and select available tools, including built-in tools and tools from MCP servers. Click **OK** to add selected tools to the agent profile.
   * To set which AI model the agent uses, add a `model:` property and select your preferred model from the autocomplete dropdown.

To update an agent profile, select **Configure Custom Agents** from the agents dropdown, and then click on an agent from the list to modify it. For more information on custom agents in VS Code, see [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents).


## Configuring an agent profile

An agent profile is a Markdown file with YAML frontmatter that specifies the custom agent's name, description, available tools, and MCP server configurations (for organization/enterprise level agents). Configuring an agent profile involves defining the agent's identity, capabilities, tool access, and behavioral instructions.

For detailed configuration information about YAML properties, tools, MCP server setup, tool aliases, and how custom agents are processed, see [Custom agents configuration](/en/copilot/reference/custom-agents-configuration).

To configure your agent profile:

1. Optionally, write a `name` for your custom agent. If unset, the name will default to the filename (without the `.md` or `.agent.md` suffix).
2. Write a brief `description` (required) explaining what your agent does and its specific capabilities or domain expertise.
3. In the `tools` property, define which tools the agent can use. This is a list of tool names or aliases, including tools from MCP servers configured in the repository settings or the agent profile (for example, `tools: ["read", "edit", "search", "some-mcp-server/tool-1"]`). If you omit this property, the agent will have access to all available tools.
4. If creating an organization or enterprise level agent on GitHub, you can use the `mcp-servers` property to optionally configure MCP servers that will be available only to this agent to extend its capabilities.
5. If you are creating and using the agent profile in VS Code, JetBrains IDEs, Eclipse, or Xcode, you can also use the `model` property to control which AI model the agent should use.
6. Optionally, set the `target` property to either `vscode` or `github-copilot` if you want to only use the agent in a specific environment. The agent will be available in both environments if you omit the property.
7. Write the agent's prompt. Define the agent's behavior, expertise, and instructions in the Markdown content below the YAML frontmatter. The prompt can be a maximum of 30,000 characters.

## Example agent profiles

The following examples demonstrate what an agent profile could look like for the common tasks of writing tests or planning the implementation of a project. For additional inspiration, see the [Custom agents](/en/copilot/tutorials/customization-library/custom-agents) examples in the customization library. You can also find more specific examples in the [awesome-copilot](https://github.com/github/awesome-copilot/tree/main/agents) community collection.

### Testing specialist

This example enables all tools by omitting the `tools` property.

```text copy
---
name: test-specialist
description: Focuses on test coverage, quality, and testing best practices without modifying production code
---

You are a testing specialist focused on improving code quality through comprehensive testing. Your responsibilities:

- Analyze existing tests and identify coverage gaps
- Write unit tests, integration tests, and end-to-end tests following best practices
- Review test quality and suggest improvements for maintainability
- Ensure tests are isolated, deterministic, and well-documented
- Focus only on test files and avoid modifying production code unless specifically requested

Always include clear test descriptions and use appropriate testing patterns for the language and framework.
```

### Implementation planner

This example only enables a subset of tools.

```text copy
---
name: implementation-planner
description: Creates detailed implementation plans and technical specifications in markdown format
tools: ["read", "search", "edit"]
---

You are a technical planning specialist focused on creating comprehensive implementation plans. Your responsibilities:

- Analyze requirements and break them down into actionable tasks
- Create detailed technical specifications and architecture documentation
- Generate implementation plans with clear steps, dependencies, and timelines
- Document API designs, data models, and system interactions
- Create markdown files with structured plans that development teams can follow

Always structure your plans with clear headings, task breakdowns, and acceptance criteria. Include considerations for testing, deployment, and potential risks. Focus on creating thorough documentation rather than implementing code.
```

## Using custom agents

Once you've created a custom agent, you can use it wherever Copilot coding agent is available.

* When prompting Copilot coding agent with a task on GitHub.com, use the dropdown menu in the agents panel or agents tab to select your custom agent instead of the default coding agent.
* When assigning Copilot coding agent to an issue, you can select your custom agent from the dropdown menu to handle the issue with your specialized configuration.
* When using the GitHub Copilot CLI, you can choose to use a particular custom agent by using the `/agent` slash command or referencing the agent in a prompt or via a command-line argument. For more information, see [Using GitHub Copilot CLI](/en/copilot/how-tos/use-copilot-agents/use-copilot-cli#use-custom-agents).

When Copilot opens pull requests, it will note which custom agent was used to complete the work in the pull request description.

For more information on using Copilot coding agent, see [Asking GitHub Copilot to create a pull request](/en/copilot/how-tos/use-copilot-agents/coding-agent/create-a-pr).

### Using custom agents in your IDE

You can also use your custom agent profiles directly in supported IDEs, including Visual Studio Code, JetBrains IDEs, Eclipse, and Xcode. You can switch between custom agents using the agent dropdown in the Chat window, allowing you to access specialized configurations for different tasks like planning, code editing, or research.

Note that some properties may function differently, or be ignored, between the GitHub.com and IDE environments. For more information on supported properties, see [Custom agents configuration](/en/copilot/reference/custom-agents-configuration#yaml-frontmatter-properties).

For more information on custom agents in VS Code specifically, see [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents) in the VS Code documentation.



# Custom agents configuration

Reference for configuring custom agents.

This reference article provides detailed configuration information for custom agents. For general information about creating custom agents, see [Creating custom agents](/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents).

> \[!NOTE]
> Custom agents are in public preview for JetBrains IDEs, Eclipse, and Xcode, and subject to change.

## YAML frontmatter properties

The following table outlines the properties that are supported in repository-level agent profiles, organization or enterprise level agent profiles, and in VS Code. The configuration file's name (minus `.md` or `.agent.md`) is used for deduplication between levels so that the lowest level configuration takes precedence.

<div class="ghd-tool rowheaders">

| Property      | Type                                                     | Purpose                                                                                                                                                                               | Repository                                                                                                                                                                                                                                                                                                                                                                                                                          | Organization / enterprise                                                                                                                                                                                                                                                                                                | VS Code, JetBrains IDEs, Eclipse, and Xcode                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | string                                                   | Display name for the custom agent. Optional.                                                                                                                                          | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            |
| `description` | **Required** string                                      | Description of the custom agent's purpose and capabilities                                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            |
| `target`      | string                                                   | Target environment or context for the custom agent (`vscode` or `github-copilot`). If unset, defaults to both environments.                                                           | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            |
| `tools`       | list of strings, string                                  | List of tool names the custom agent can use. Supports both a comma separated string and yaml string array. If unset, defaults to all tools. See [Tools](#tools).                      | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            |
| `infer`       | boolean                                                  | Controls whether Copilot coding agent can automatically use this custom agent based on task context. When `false`, the agent must be manually selected. If unset, defaults to `true`. | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            |
| `mcp-servers` | object                                                   | Additional MCP servers and tools that should be used by the custom agent.                                                                                                             | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-x" aria-label="Not supported" role="img"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.749.749 0 0 1 1.275.326.749.749 0 0 1-.215.734L9.06 8l3.22 3.22a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L8 9.06l-3.22 3.22a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-x" aria-label="Not supported" role="img"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.749.749 0 0 1 1.275.326.749.749 0 0 1-.215.734L9.06 8l3.22 3.22a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L8 9.06l-3.22 3.22a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"></path></svg> |
| `metadata`    | object consisting of a name and value pair, both strings | Allows annotation of the agent with useful data                                                                                                                                       | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg>                                                                                                            | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-check" aria-label="Supported" role="img"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> | <svg version="1.1" width="16" height="16" viewBox="0 0 16 16" class="octicon octicon-x" aria-label="Not supported" role="img"><path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.749.749 0 0 1 1.275.326.749.749 0 0 1-.215.734L9.06 8l3.22 3.22a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L8 9.06l-3.22 3.22a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z"></path></svg> |

</div>

Define the agent's behavior, expertise, and instructions in the Markdown content below the YAML frontmatter. The prompt can be a maximum of 30,000 characters.

> \[!NOTE]
> The `model`, `argument-hint`, and `handoffs` properties from VS Code and other IDE custom agents are currently not supported for Copilot coding agent on GitHub.com. They are ignored to ensure compatibility. For more information on custom agent file structure in VS Code, see [Custom agents in VS Code](https://code.visualstudio.com/docs/copilot/customization/custom-agents#_custom-agent-file-structure) in the VS Code documentation.

## Tools

The custom agent `tools` property controls which tools are available to your agent, including those from MCP servers.

While you cannot configure MCP servers directly within an agent profile for repository-level custom agents, your custom agent will have access to MCP server tools that have been configured in the repository settings. For more information on configuring MCP servers for coding agent in a repository, see [Extending GitHub Copilot coding agent with the Model Context Protocol (MCP)](/en/copilot/how-tos/use-copilot-agents/coding-agent/extend-coding-agent-with-mcp).

You can configure `tools` using the following approaches:

* **Enable all available tools**: Omit the `tools` property entirely or use `tools: ["*"]` to enable all available tools. This will include all MCP server tools configured in the repository settings.
* **Enable specific tools**: Provide a list of specific tool names or aliases (for example, `tools: ["read", "edit", "search"]`) to enable only those tools. For available tool aliases, see [Tool aliases](#tool-aliases) below.
  * Note that if your repository has MCP servers configured, you can choose to make only specific tools from those servers available to your custom agent. Tool names from specific MCP servers can be prefixed with the server name followed by a `/`. For example, `some-mcp-server/some-tool`.
  * You can also explicitly enable all tools from a specific MCP server using `some-mcp-server/*`.
  * Tools from VS Code extensions can use the extension name as a proxy, like `azure.some-extension/some-tool`.
* **Disable all tools**: Use an empty list (`tools: []`) to disable all tools for the agent.

All unrecognized tool names are ignored, which allows product-specific tools to be specified in an agent profile without causing problems.

### Tool aliases

The following tool aliases are available for custom agents. All aliases are case insensitive:

| Primary alias | Compatible aliases                           | Coding agent mapping                                 | Purpose                                                                                                   |
| ------------- | -------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `execute`     | `shell`, `Bash`, `powershell`                | Shell tools: `bash` or `powershell`                  | Execute a command in the appropriate shell for the operating system.                                      |
| `read`        | `Read`, `NotebookRead`                       | `view`                                               | Read file contents.                                                                                       |
| `edit`        | `Edit`, `MultiEdit`, `Write`, `NotebookEdit` | Edit tools: e.g. `str_replace`, `str_replace_editor` | Allow LLM to edit. Exact arguments can vary.                                                              |
| `search`      | `Grep`, `Glob`                               | `search`                                             | Search for files or text in files.                                                                        |
| `agent`       | `custom-agent`, `Task`                       | "Custom agent" tools                                 | Allows a different custom agent to be invoked to accomplish a task.                                       |
| `web`         | `WebSearch`, `WebFetch`                      | Currently not applicable for coding agent.           | Allows fetching content from URLs and performing a web search                                             |
| `todo`        | `TodoWrite`                                  | Currently not applicable for coding agent.           | Creates and manages structured task lists. Not supported in coding agent today, but supported by VS Code. |

### Tool names for "out-of-the-box" MCP servers

The following MCP servers are available out-of-box for Copilot coding agent and can be referenced using namespacing:

| MCP server name | Available tools                                                                                                                                                                                                                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `github`        | All read-only tools are available by default, but the token the server receives is scoped to the source repository. `github/*` includes all of them, or you can reference `github/<tool name>` where `<tool name>` is a value from the MCP server documentation.                                                                          |
| `playwright`    | All playwright tools are available by default, but the server is configured to only access localhost. `playwright/*` includes all of them, or you can reference `playwright/<tool name>` where `<tool name>` is a value from the MCP server documentation. By default the token it has access to is scoped to the source code repository. |

## MCP server configuration details

> \[!NOTE]
> MCP servers can only be configured directly within custom agent profiles at the organization and enterprise level. Repository-level custom agents cannot have MCP servers configured directly in their profiles, but can use tools from MCP servers configured in the repository's settings.

The following sample agent profile shows an organization-level agent with MCP server and secret configured. Additionally, only one tool from the MCP server has been enabled in the `tools` property in the YAML frontmatter:

```text
---
name: my-custom-agent-with-mcp
description: Custom agent description
tools: ['tool-a', 'tool-b', 'custom-mcp/tool-1']
mcp-servers:
  custom-mcp:
    type: 'local'
    command: 'some-command'
    args: ['--arg1', '--arg2']
    tools: ["*"]
    env:
      ENV_VAR_NAME: $
---

Prompt with suggestions for behavior and output
```

The `mcp-servers` property in an agent profile is a YAML representation of the JSON configuration format used to configure MCP servers for Copilot coding agent.

Most sub-properties are the same as the JSON representation. The following sections describe changes from the initial implementation of MCP configuration in Copilot coding agent that are relevant to custom agents. For more information about the JSON configuration format, see [Extending GitHub Copilot coding agent with the Model Context Protocol (MCP)](/en/copilot/how-tos/use-copilot-agents/coding-agent/extend-coding-agent-with-mcp#writing-a-json-configuration-for-mcp-servers).

### MCP server type

For compatibility, the `stdio` type used by Claude Code and VS Code is mapped to coding agent's `local` type.

### MCP server environment variables and secrets

> \[!NOTE]
> If your MCP server requires secrets or environment variables, these must be configured in the Copilot environment in each repository where the custom agent will be used. For more information on setting up environment variables, see [Customizing the development environment for GitHub Copilot coding agent](/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment#setting-environment-variables-in-copilots-environment).

Custom agent MCP configuration supports the same environment variable and secret replacement capabilities as existing repository-level MCP configurations. Similar to repository-level configurations, secrets and variables can be sourced from the "copilot" environment in the repository's settings. The syntax for referencing these values has been expanded to support common patterns used in GitHub Actions and Claude Code.

Both the repository-level MCP JSON configuration and the custom agent YAML configuration support the following syntax patterns:

* `COPILOT_MCP_ENV_VAR_VALUE` - Environment variable only (not recommended due to header differences)
* `$COPILOT_MCP_ENV_VAR_VALUE` - Environment variable and header
* `${COPILOT_MCP_ENV_VAR_VALUE}` - Environment variable and header (Claude Code syntax)

The custom agent YAML configuration supports the following additional syntax patterns:

* `${{ secrets.COPILOT_MCP_ENV_VAR_VALUE }}` - Environment variable and header
* `${{ var.COPILOT_MCP_ENV_VAR_VALUE }}` - Environment variable and header

## Example agent profile configurations

The following examples demonstrate what an agent profile could look like for the common tasks of writing tests or planning the implementation of a project. For additional inspiration, see the [Custom agents](/en/copilot/tutorials/customization-library/custom-agents) examples in the customization library. You can also find more specific examples in the [awesome-copilot](https://github.com/github/awesome-copilot/tree/main/agents) community collection.

### Testing specialist

This example enables all tools by omitting the `tools` property.

```text copy
---
name: test-specialist
description: Focuses on test coverage, quality, and testing best practices without modifying production code
---

You are a testing specialist focused on improving code quality through comprehensive testing. Your responsibilities:

- Analyze existing tests and identify coverage gaps
- Write unit tests, integration tests, and end-to-end tests following best practices
- Review test quality and suggest improvements for maintainability
- Ensure tests are isolated, deterministic, and well-documented
- Focus only on test files and avoid modifying production code unless specifically requested

Always include clear test descriptions and use appropriate testing patterns for the language and framework.
```

### Implementation planner

This example only enables a subset of tools.

```text copy
---
name: implementation-planner
description: Creates detailed implementation plans and technical specifications in markdown format
tools: ["read", "search", "edit"]
---

You are a technical planning specialist focused on creating comprehensive implementation plans. Your responsibilities:

- Analyze requirements and break them down into actionable tasks
- Create detailed technical specifications and architecture documentation
- Generate implementation plans with clear steps, dependencies, and timelines
- Document API designs, data models, and system interactions
- Create markdown files with structured plans that development teams can follow

Always structure your plans with clear headings, task breakdowns, and acceptance criteria. Include considerations for testing, deployment, and potential risks. Focus on creating thorough documentation rather than implementing code.
```

## Processing of custom agents

### Custom agents names

In the case of naming conflicts, the lowest level configuration overrides higher-level configurations. This means that a repository-level agent would take precedence over an organization-level agent, and the organization-level agent would override an enterprise-level agent.

### Versioning

Custom agent versioning is based on Git commit SHAs for the agent profile file. This allows you to create branches or tags with different versions of custom agents as needed. When you assign a custom agent to a task, the custom agent will be instantiated using the latest version of the agent profile for that repository and branch. When the agent creates a pull request, interactions within the pull request use the same version of the custom agent for consistency.

### Tools processing

The `tools` list filters the set of tools that are made available to the agent - whether built-in or sourced from MCP servers. When you configure tools in your agent profile, the behavior depends on what you specify:

* If no tools are specified, all available tools are enabled
* An empty tools list (`tools: []`) disables all tools
* A specific list (`tools: [...]`) enables only those tools

### MCP server configurations

For MCP server configurations, there is a specific processing order that ensures proper override behavior: out-of-the-box MCP configurations (like the GitHub MCP) are processed first, followed by the custom agent MCP configuration (supported for organization or enterprise level custom agents only), and finally repository-level MCP configurations. This allows each level to override settings from the previous level as appropriate.