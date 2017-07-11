# -*- coding: utf-8 -*-

"""
    config
    ~~~~~~

    Implements config

    :author:    Feei <feei@feei.cn>
    :homepage:  https://github.com/wufeifei/cobra
    :license:   MIT, see LICENSE for more details.
    :copyright: Copyright (c) 2017 Feei. All rights reserved
"""
import os
import json
import StringIO
import ConfigParser
import traceback
from xml.etree import ElementTree
from .log import logger

project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
core_path = os.path.join(project_directory, 'cobra')
tests_path = os.path.join(core_path, 'tests')
examples_path = os.path.join(tests_path, 'examples')
rules_path = os.path.join(project_directory, 'rules')
home_path = os.path.join(os.path.expandvars(os.path.expanduser("~")), ".cobra")
config_path = os.path.join(home_path, 'config.cobra')
rule_path = os.path.join(home_path, 'rule.cobra')


def to_bool(value):
    """
       Converts 'something' to boolean. Raises exception for invalid formats
           Possible True  values: 1, True, "1", "TRue", "yes", "y", "t"
           Possible False values: 0, False, None, [], {}, "", "0", "faLse", "no", "n", "f", 0.0, ...
    """
    if str(value).lower() in ("yes", "y", "true", "t", "1"):
        return True
    if str(value).lower() in ("no", "n", "false", "f", "0", "0.0", "", "none", "[]", "{}"):
        return False
    raise Exception('Invalid value for boolean conversion: ' + str(value))


class Config(object):
    def __init__(self, level1=None, level2=None):
        self.level1 = level1
        self.level2 = level2
        if level1 is None and level2 is None:
            return
        config = ConfigParser.ConfigParser()

        config.read(config_path)
        value = None
        try:
            value = config.get(level1, level2)
        except Exception as e:
            print(level1, level2)
            traceback.print_exc()
            print("./configs file configure failed.\nError: {0}\nSee Help: http://cobra-docs.readthedocs.io/en/latest/configuration/".format(e.message))
        self.value = value

    @staticmethod
    def copy(source, destination):
        if os.path.isfile(destination) is not True:
            logger.info('Not set configuration, setting....')
            with open(source) as f:
                content = f.readlines()
            with open(destination, 'w+') as f:
                f.writelines(content)
            logger.info('Config file set success(~/.cobra/{source})'.format(source=source))
        else:
            return

    def initialize(self):
        # ~/.cobra/config.cobra
        source_config = os.path.join(project_directory, 'config.cobra')
        self.copy(source_config, config_path)

        # ~/.cobra/rule.cobra
        destination_rule = os.path.join(project_directory, 'rule.cobra')
        self.copy(destination_rule, rule_path)
        return

    def rule(self):
        self.initialize()
        try:
            with open(rule_path) as f:
                rules = json.load(f)
            return rules
        except Exception, v:
            logger.critical(v.message)
            return []


def properties(config_path):
    if os.path.isfile(config_path) is not True:
        return dict()
    with open(config_path) as f:
        config = StringIO.StringIO()
        config.write('[dummy_section]\n')
        config.write(f.read().replace('%', '%%'))
        config.seek(0, os.SEEK_SET)

        cp = ConfigParser.SafeConfigParser()
        cp.readfp(config)

        return dict(cp.items('dummy_section'))


class Rules(object):
    def __init__(self):
        self.rules_path = rules_path

    @property
    def languages(self):
        """
        Read all language extensions
        :return:
        {
            'pph':[
                '.php',
                '.php3',
                '.php4',
                '.php5'
            ]
        }
        """
        language_extensions = {}
        xml_languages = self._read_xml('languages.xml')
        if xml_languages is None:
            logger.critical('languages read failed!!!')
            return None
        for language in xml_languages:
            l_name = language.get('name').lower()
            language_extensions[l_name] = []
            for lang in language:
                l_ext = lang.get('value').lower()
                language_extensions[l_name].append(l_ext)
        return language_extensions

    @property
    def frameworks(self):
        """
        Read all framework rules
        :return: dict
        """
        frameworks_rules = {}
        xml_frameworks = self._read_xml('frameworks.xml')
        if xml_frameworks is None:
            logger.critical('frameworks read failed!!!')
            return None
        for framework in xml_frameworks:
            f_name = framework.get('name').lower()
            f_lang = framework.get('language').lower()
            f_code = framework.get('code')
            framework_info = {
                f_name: {
                    'code': f_code,
                    'rules': []
                }
            }
            frameworks_rules[f_lang] = framework_info
            for rule in framework:
                rule_info = {rule.tag: rule.get('value')}
                frameworks_rules[f_lang][f_name]['rules'].append(rule_info)
        return frameworks_rules

    @property
    def vulnerabilities(self):
        """
        Read all vulnerabilities information
        :return:
        """
        vulnerabilities_info = {}
        xml_vulnerabilities = self._read_xml('vulnerabilities.xml')
        if xml_vulnerabilities is None:
            logger.critical('vulnerabilities read failed!!!')
            return None
        for vulnerability in xml_vulnerabilities:
            v_id = int(vulnerability.get('vid'))
            v_name = vulnerability.get('name').lower()
            v_level = int(vulnerability.get('level'))
            v_description = vulnerability[0].text.strip()
            v_repair = vulnerability[1].text.strip()
            vulnerabilities_info[str(v_id)] = {
                'name': v_name,
                'description': v_description,
                'level': v_level,
                'repair': v_repair,
            }
        return vulnerabilities_info

    @property
    def rules(self):
        """
        Get all rules
        :return:
         {
            'XSS': [
                # single rule
                {
                    'status': True,
                    'name': {
                        'zh-cn': "FanShe XSS",
                        'en': "Reflect XSS"
                    },
                    'vid': '10010',
                    'author': 'Feei <feei@feei.cn>',
                    'file': 'reflect.php.xml',
                    'test': {
                        'false': [
                            'code test case1',
                            'code test case2'
                        ],
                        'true': [
                            'code test case 1',
                            'code test case 2'
                        ]
                    },
                    'rule': [
                        'match regex 1',
                        'match regex 2',
                        'repair regex 3'
                    ],
                    'language': 'php'
                }
            ]
         }
        """
        vulnerabilities = []
        for vulnerability_name in os.listdir(self.rules_path):
            v_path = os.path.join(self.rules_path, vulnerability_name)
            if os.path.isfile(v_path):
                continue
            for rule_filename in os.listdir(v_path):
                v_rule_path = os.path.join(v_path, rule_filename)
                if os.path.isfile(v_rule_path) is not True:
                    continue
                # rule information
                rule_info = {
                    'name': {},
                    'file': rule_filename,
                    'test': {
                        'true': [],
                        'false': []
                    },
                    'language': rule_filename.split('.xml')[0].split('.')[1],
                    'block': '',
                    'repair': '',
                }
                rule_path = os.path.join(vulnerability_name, rule_filename)
                xml_rule = self._read_xml(rule_path)
                if xml_rule is None:
                    logger.critical('rule read failed!!! ({file})'.format(file=rule_path))
                    continue
                for x in xml_rule:
                    if x.tag == 'vid':
                        rule_info['vid'] = x.get('value')
                    if x.tag == 'name':
                        lang = x.get('lang').lower()
                        rule_info['name'][lang] = x.text.strip()
                    if x.tag == 'status':
                        rule_info['status'] = to_bool(x.get('value'))
                    if x.tag == 'author':
                        name = x.get('name')
                        email = x.get('email')
                        rule_info['author'] = '{name}<{email}>'.format(name=name, email=email)
                    if x.tag in ['match', 'repair']:
                        rule_info[x.tag] = x.text.strip()
                    if x.tag == 'test':
                        for case in x:
                            case_ret = case.get('assert').lower()
                            case_test = case.text.strip()
                            if case_ret in ['true', 'false']:
                                rule_info['test'][case_ret].append(case_test)
                vulnerabilities.append(rule_info)
        return vulnerabilities

    def _read_xml(self, filename):
        """
        Read XML
        :param filename:
        :return:
        """
        path = os.path.join(self.rules_path, filename)
        try:
            tree = ElementTree.parse(path)
            return tree.getroot()
        except Exception as e:
            logger.warning('parse xml failed ({file})'.format(file=path))
            return None


class Vulnerabilities(object):
    def __init__(self, key):
        self.key = key

    def status_description(self):
        status = {
            0: 'Not fixed',
            1: 'Not fixed(Push third-party)',
            2: 'Fixed'
        }
        if self.key in status:
            return status[self.key]
        else:
            return False

    def repair_description(self):
        repair = {
            0: 'Initialize',
            1: 'Fixed',
            4000: 'File not exist',
            4001: 'Special file',
            4002: 'Whitelist',
            4003: 'Test file',
            4004: 'Annotation',
            4005: 'Modify code',
            4006: 'Empty code',
            4007: 'Const file',
            4008: 'Third-party'
        }
        if self.key in repair:
            return repair[self.key]
        else:
            return False

    def level_description(self):
        level = {
            0: 'Undefined',
            1: 'Low',
            2: 'Medium',
            3: 'High',
        }
        if self.key in level:
            return level[self.key]
        else:
            return False
