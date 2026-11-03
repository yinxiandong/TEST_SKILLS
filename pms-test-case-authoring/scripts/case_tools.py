"""Portable local test-case authoring CLI. No PMS writes or test execution."""
import argparse
import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

HEADERS = ['用例类型','特性模块','所属端','一级特性','二级特性','三级特性','四级特性','用例名称','用例编号','用例级别','预置条件','执行步骤','预期结果','标签（版本号/现网问题）','需求名称/现网问题单号','是否可自动化','是否已自动化','是否发必测','用例维护人','修订记录','备注','测试责任人','计划日期','执行日期','执行结果','执行结果备注','截图1','截图2','截图3','截图4','截图5']
WIDTHS = [18,14,16,18,20,22,18,34,38,12,62,76,76,18,22,14,14,14,18,16,42,16,16,16,20,20,14,14,14,14,14]
MAPPING = ['requirementCode','localCaseNo','pmsCaseId','repoPath','featurePath','sourceRef','coverageRefs','disposition']
CHECKLIST = '# 通用测试检查清单\n\n- 固定已接受来源与版本，核对现有用例复用。\n- 按风险覆盖核心流程、边界、异常、权限、国际化和恢复。\n- 每步预期可观察，数据与角色明确，未知阈值有待确认说明。\n- 异步验证终态与产物，文件验证内容和业务关联。\n- 31列固定，需求列只填编号，映射可追溯。\n- 新用例执行结果为空；实际结论绑定版本、环境及运行证据。\n'


def safe_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('名称必须是非空字符串')
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).strip().rstrip('. ')
    if not value or value in ('.', '..') or value.split('.')[0].upper() in {'CON','PRN','AUX','NUL', *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}:
        raise ValueError('名称无效或是系统保留名称')
    return value


def text(value):
    if isinstance(value, list):
        return '\n'.join(f'{i}、{item}' for i, item in enumerate(value, 1))
    return str(value)


def load_cases(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('输入必须是JSON对象')
    meta, cases = data.get('metadata'), data.get('cases')
    if not isinstance(meta, dict) or not isinstance(cases, list) or not cases:
        raise ValueError('需要metadata对象和非空cases列表')
    for key in ('product','version','requirementCode','requirementName'):
        if not isinstance(meta.get(key), str) or not meta[key].strip():
            raise ValueError(f'metadata.{key}必须为非空字符串')
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+', meta['requirementCode']):
        raise ValueError('requirementCode只能包含需求编号，不得包含名称或说明')
    rows, mapping, seen = [], [], set()
    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict):
            raise ValueError(f'第{index}条必须为对象')
        unknown = set(case) - set(HEADERS) - {'mapping'}
        if unknown:
            raise ValueError(f'第{index}条未知字段：{sorted(unknown)}')
        row = dict(case)
        defaults = {'用例类型':'基线测试用例','标签（版本号/现网问题）':f"{meta['product']} {meta['version']}",'需求名称/现网问题单号':meta['requirementCode'],'是否可自动化':'否','是否已自动化':'否','是否发必测':'是','修订记录':'新增'}
        for key, value in defaults.items():
            row.setdefault(key, value)
        for key in HEADERS[:13]:
            if key not in row or not row[key]:
                raise ValueError(f'第{index}条缺少{key}')
        code = row['用例编号']
        if not isinstance(code, str) or not re.fullmatch(r'[A-Z0-9]+-[A-Z0-9]+-P[0-5]-\d{3,}', code):
            raise ValueError(f'第{index}条用例编号格式错误')
        if code in seen:
            raise ValueError(f'重复用例编号：{code}')
        seen.add(code)
        if row['用例级别'] not in [f'P{i}' for i in range(6)] or f"-{row['用例级别']}-" not in code:
            raise ValueError(f'{code}级别与编号不一致')
        for key in ('预置条件','执行步骤','预期结果'):
            if not isinstance(row[key], list) or not row[key] or any(not isinstance(v,str) or not v.strip() for v in row[key]):
                raise ValueError(f'{code}的{key}须为非空字符串数组')
        if len(row['执行步骤']) != len(row['预期结果']):
            raise ValueError(f'{code}步骤与预期数量不一致')
        if row['需求名称/现网问题单号'] != meta['requirementCode']:
            raise ValueError(f'{code}需求编号与metadata不一致')
        for key in ('是否可自动化','是否已自动化','是否发必测'):
            if row[key] not in ('是','否'):
                raise ValueError(f'{code}的{key}只能为是或否')
        if row['修订记录'] not in ('新增','修改'):
            raise ValueError(f'{code}修订记录须为新增或修改')
        if any(row.get(k) for k in HEADERS[22:]):
            raise ValueError(f'{code}含计划/执行数据；生成器只处理设计，已有执行记录请单独保留')
        link = case.get('mapping', {})
        if not isinstance(link, dict) or set(link) - set(MAPPING[2:]):
            raise ValueError(f'{code}的mapping字段无效')
        if link.get('disposition') not in ('复用','修改','新增','待确认'):
            raise ValueError(f'{code}须明确mapping.disposition')
        if not isinstance(link.get('sourceRef'), str) or not link['sourceRef'].strip():
            raise ValueError(f'{code}缺少mapping.sourceRef')
        if row['是否已自动化'] == '是' and not row.get('备注'):
            raise ValueError(f'{code}已自动化须在备注提供脚本和证据位置')
        values = []
        for key in HEADERS:
            value = text(row.get(key, ''))
            if len(value) > 32767 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', value):
                raise ValueError(f'{code}的{key}超出Excel长度或含非法控制字符')
            values.append(value)
        rows.append(values)
        mapping.append([meta['requirementCode'],code,*[text(link.get(k,'')) for k in MAPPING[2:]]])
    return meta, rows, mapping


def write_csv(path, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        # Guard formula injection when CSV is opened directly in Excel.
        writer.writerows([["'" + v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in row] for row in rows])


def init_workspace(root):
    common = Path(root).resolve() / '公用'
    common.mkdir(parents=True, exist_ok=True)
    template = common / '用例字段模板.csv'
    if template.exists():
        with template.open(encoding='utf-8-sig', newline='') as handle:
            if list(csv.reader(handle)) != [HEADERS]:
                raise ValueError(f'已有模板不一致，保留原文件：{template}')
    else:
        write_csv(template, [HEADERS])
    checklist = common / '通用测试检查清单.md'
    if not checklist.exists():
        checklist.write_text(CHECKLIST, encoding='utf-8')
    print(json.dumps({'commonDir':str(common),'status':'initialized-or-reused'}, ensure_ascii=False))


def build(args):
    meta, rows, mapping = load_cases(args.input)
    output = Path(args.output_dir).resolve()
    filename = safe_name(f"{meta['product']}{meta['version']}_{meta['requirementName']}_测试用例")
    workbook = output / (filename + '.' + args.format)
    links = output / 'case-mapping.csv'
    report = output / 'validation-report.json'
    for path in (workbook, links, report):
        if path.exists():
            raise ValueError(f'输出已存在，请选择新的输出目录以保留历史：{path}')
    wb = None
    if args.format == 'xlsx':
        try:
            import openpyxl
            from openpyxl.styles import Alignment, Font, PatternFill
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise ValueError('缺少openpyxl，请安装requirements.txt或显式使用--format csv')
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '测试用例'
        for r, values in enumerate([HEADERS, *rows], 1):
            for c, value in enumerate(values, 1):
                cell = ws.cell(r,c,value)
                cell.data_type = 's'
                cell.font = Font(name='微软雅黑',size=10,bold=r==1,color='FFFFFF' if r==1 else '000000')
                cell.alignment = Alignment(horizontal='center' if r==1 else 'left',vertical='center' if r==1 else 'top',wrap_text=True)
                if r == 1:
                    cell.fill = PatternFill('solid',fgColor='FF1F4E78')
            ws.row_dimensions[r].height = 32 if r==1 else 90
        for c, width in enumerate(WIDTHS,1):
            ws.column_dimensions[get_column_letter(c)].width = width
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = f'A1:AE{len(rows)+1}'
    output.mkdir(parents=True,exist_ok=True)
    try:
        if wb:
            with workbook.open('xb') as handle:
                wb.save(handle)
            wb.close()
        else:
            write_csv(workbook,[HEADERS,*rows])
        write_csv(links,[MAPPING,*mapping])
        with report.open('x',encoding='utf-8') as handle:
            json.dump({'valid':True,'caseCount':len(rows),'columns':31,'requirementCode':meta['requirementCode'],'format':args.format,'scope':'structural validation; business review and test execution not performed'},handle,ensure_ascii=False,indent=2)
    finally:
        if wb:
            wb.close()
    print(json.dumps({'output':str(workbook),'caseCount':len(rows),'mapping':str(links)},ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    init = sub.add_parser('init')
    init.add_argument('--workspace',required=True)
    validate = sub.add_parser('validate')
    validate.add_argument('--input',required=True)
    generate = sub.add_parser('build')
    generate.add_argument('--input',required=True)
    generate.add_argument('--output-dir',required=True)
    generate.add_argument('--format',choices=['xlsx','csv'],default='xlsx')
    args = parser.parse_args()
    try:
        if args.command == 'doctor':
            print(json.dumps({'python':sys.version.split()[0],'openpyxl':bool(importlib.util.find_spec('openpyxl'))}))
        elif args.command == 'init':
            init_workspace(args.workspace)
        elif args.command == 'validate':
            meta, rows, _ = load_cases(args.input)
            print(json.dumps({'valid':True,'caseCount':len(rows),'requirementCode':meta['requirementCode']},ensure_ascii=False))
        else:
            build(args)
    except (ValueError,OSError,json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
