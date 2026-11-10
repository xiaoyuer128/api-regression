# API Regression

## 新增：脱敏诊断与可运行服务

执行报告新增 case_id、耗时、预期状态及本地复现提示；请求路径优先显示文档模板，无模板时遮蔽。Schema 诊断仅记录规则与路径深度，避免输出数据值及动态字段名。规范中的模板本身仍需审查；生成清单及 pytest 文件包含样例值，不能视为脱敏报告。

可运行库存示例：`python examples/demo_service.py`。它是自建演示服务，不是生产项目，包含正确接口 `/items/2?q=demo` 和故意返回错误 id 类型的 `/broken?q=demo`。测试实际启动该服务，验证成功、回归检出、缺参数探索及敏感查询值不出现在报告中。

[Schemathesis 后端评估](docs/SCHEMATHESIS.md)已记录接入条件，尚未实现适配器，不宣称已接入。

[简体中文](README.md) | [English](README.en.md)

从 OpenAPI 生成可审阅的 GET 接口测试清单，在明确授权的本地服务上执行状态码与 JSON 响应契约检查，并导出 pytest。

## 安装与使用

Python 3.10+，命令相对于仓库根目录。生成和导出不会发请求。

```console
python -m pip install -r requirements.txt
python scripts/api_regression.py --spec examples/openapi.json
python scripts/api_regression.py --spec examples/openapi.json --export-pytest test_generated.py
python -m unittest discover -s tests -v
python evals/run_rounds.py
```

服务需另行启动。确认 GET 操作只读后执行：

```console
python scripts/api_regression.py --spec examples/openapi.json --base-url http://127.0.0.1:8000 --approve-read-only
```

导出的 pytest 需设置 API_REGRESSION_SCRIPT（脚本完整路径）、API_REGRESSION_BASE_URL，以及 API_REGRESSION_APPROVED=1；缺少授权会跳过。运行 `python -m pytest --rootdir . test_generated.py -q`，探索用例明确跳过，不构造虚假断言。

## 支持范围

- OpenAPI 3.0.0–3.0.3 JSON；GET；显式数字响应状态码。
- query/path 标量参数，使用文档提供的合法 example、enum 或 default，不猜业务值；支持 operation 覆盖 path 级参数。
- 缺少必填 query 参数生成 exploratory 用例，其响应只记录 observed，不猜测必须返回 400。
- application/json 响应使用明确列出的 Schema 子集检查：type、properties、required、additionalProperties、items、enum、minimum/maximum、长度/元素数及 pattern；使用兼容子集的 Draft4 校验器，不把 OAS 3.0 全部当 JSON Schema。
- 仅 HTTP 127.0.0.1，无代理、不跟随重定向；默认超时 3 秒、上限 30 秒，最多 100 用例，响应体读取上限 1 MiB。

未支持：鉴权、变更操作、header/cookie 参数、数组/对象参数、复杂序列化、引用、nullable/composition/format 等其他 Schema 关键字、YAML、default/范围状态码和完整 OAS 规范校验。操作使用不支持功能时记录 skipped；畸形文档可能返回配置错误。

## 报告与退出码

passed 为契约通过，failed 为状态/响应不匹配，error 为请求失败，observed 为无精确预期的探索结果；skipped 单列。报告不保存响应正文、查询值或鉴权值，但路径可能包含样例标识，发布前仍应审查。

0 表示没有已执行失败，也可能是只生成或全跳过；1 表示存在 failed/error；2 表示输入配置错误。必须检查实际执行数量，不把全跳过当覆盖完成。响应状态集合只证明文档契约，不证明业务健康。

## 验证与限制

三轮记录见 [results.json](evals/results.json)，覆盖真实临时 HTTP 服务、状态失败、响应类型失败、重定向、参数编码/继承、授权/地址/数量/超时限制，以及导出 pytest 的实际执行。

测试不是穷尽证明，重复轮次不增加覆盖。尚无独立 Agent 试验；没有真实生产 API、认证、超时慢流或恶意响应的全面评测。JSON 解析沿用 Python 默认行为，极端数值、重复键与资源安全需要后续加固，不应用于不可信服务。执行网络请求有副作用的可能，GET 也必须先确认语义。

## 开发与发布

[开发流程](docs/DEVELOPMENT.md)；[评测说明](evals/README.md)。当前已完成限定范围的本地实现，独立仓库为 https://github.com/xiaoyuer128/api-regression 。

参考 [OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3) 的参数、响应和操作定义；同类候选 [api-tester](https://github.com/zeroclaw-labs/zeroclaw-skills/blob/master/skills/api-tester/SKILL.md) 尚未完成源码/Star 核验，不宣称评测优劣。
