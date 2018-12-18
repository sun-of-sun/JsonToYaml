import os
import yaml,json
import re
def seach_list(Str):
    result = re.findall(r'([.*?])',Str)
    if(len(result)==0):
        return False
    else:
        return True
def cmp(pm_json,Yaml_script):
    #递归遍历获取pm.json中的所有接口
    if isinstance(pm_json, dict):
        if pm_json.get('info',{}):
            #- config:
            Yaml_script.write('- config:'+'\n'+' '*4+'name: '+pm_json['info']['name']+'\n'+' '*4+'variables: #全局变量参数'+'\n'+' '*4+'request: '+'\n'+' '*8+'base_url: ')
            pm_json['info'] = {}
            cmp(pm_json, Yaml_script)
        else:
            #- test：
            for key in pm_json:
                if 'request' == key:
                    Yaml_script.write('\n'+"- test:"+'\n')
                    #name:
                    Yaml_script.write(' ' * 4 +'name'+':' + ' '+str(pm_json['name'])+'\n')
                    #request:
                    Yaml_script.write(' ' * 4 +"request:"+"\n")
                    raw = pm_json[key]['url']['raw']
                    method = raw.replace('{{', '$').replace('}}','')
                    #url:
                    Yaml_script.write(' ' * 8  + 'url' + ':' +' '+ method + "\n")
                    #method:
                    Yaml_script.write(' ' * 8  + 'method'+':'+' '+pm_json[key]['method']+ "\n")
                    #json:
                    if 'raw' in pm_json[key]['body']:
                        if pm_json[key]['body']:
                            if pm_json[key]['body']['raw']:
                                raw2 = str(pm_json[key]['body']['raw'])
                                body = raw2.replace('"{{','"$').replace('}}"', '"').replace('{{', '"$').replace('}}', '"').replace('null','"null"').replace('true','"true"').replace('"raw": ""','"raw":"null"').replace('false','"false"')
                                Yaml_script.write(' ' * 8 + 'json'+':'+'\n')

                                #跳过异常
                                try:
                                    for k,v in eval(body).items():
                                        if '$' in str(v):
                                            Yaml_script.write(' ' * 12 +str(k)+':'+' '+str(v)+'\n')
                                        else:
                                            Yaml_script.write(' ' * 12 +str(k) + ':' + ' ' +'"'+str(v) +'"'+'\n')
                                except(SyntaxError,AttributeError):
                                    pass
                    if pm_json[key]['header']:
                        Yaml_script.write(' ' * 8 + 'headers: ' + '\n')
                        for i in pm_json[key]['header']:
                            Yaml_script.write(' ' * 12 +i['key']+':'+' '+i['value']+'\n')
                    if pm_json.get('event', None):
                        event = get_event_content(pm_json['event'])
                        if event[2]:
                            Yaml_script.write(' ' * 4 + 'extract:' + '\n')
                            for k,v in event[2].items():
                                Yaml_script.write(' ' * 8 +'- '+k+': '+v+'\n')
                        Yaml_script.write(' ' * 4 +'validate:'+'\n'+' ' * 8 +'- eq: [status_code, 200]'+'\n'+' ' * 8 +'- eq: [content.status, SUCCESS]'+'\n')
                        if event[1]:
                            for k,v in event[1].items():
                                Yaml_script.write(' ' * 8 +'- eq: '+'['+str(k)+','+' '+str(v)+']'+'\n')
                        if event[0]:
                            Yaml_script.write(' ' * 4 +'variables:'+'\n')
                            for k,v in event[0].items():
                                Yaml_script.write(' ' * 8 +'- '+ k+': '+v+'\n')
                else:
                    cmp(pm_json[key],Yaml_script)
    elif isinstance(pm_json, list):
        for i in pm_json:
            cmp(i,Yaml_script)
#传参数据处理
def get_event_content(event_content):
    """
    event 模块
    :param event_content:
    :return: variables_res把结果添加到test['variables']中,validate_res把结果写入test['validate'], extract_res把结果写入test['extract']
    """
    variables_res = {}
    validate_res = {}
    extract_res = {}
    if event_content:
        for item in event_content:
            # variables 数据准备
            if item['listen'] == 'prerequest':
                exec_content = item['script']['exec']
                for exec_item in exec_content:
                    result = re.findall('.set\("(.*)",(.*)\);', exec_item)
                    if result:
                        for result_item in result:
                            variables_key = result_item[0].strip()
                            variables_value = result_item[1].strip('"').replace("'","").strip()
                            variables_res[variables_key] = variables_value
                            if variables_value.isdigit():
                                variables_res[variables_key] = int(variables_value)
            # validate 和 extract数据处理
            elif item['listen'] == 'test':
                exec_content = item['script']['exec']
                for validate_item in exec_content:
                    # validate 测试结果验证，数据处理
                    validate_result = re.findall('expect\(\w*\.?(.*)\)\.to\.eql\((.*)\)', validate_item.replace(' ', ''))
                    if validate_result:
                        for result_item in validate_result:
                            res_item = result_item[0].replace('[', '.').replace(']', '')
                            validate_key = 'content.'+ res_item
                            validate_value = result_item[1].strip('"')
                            validate_res[validate_key] = validate_value
                            if validate_value.isdigit():
                                validate_res[validate_key] = int(validate_value)
                    # extract 保存response指定参数，数据处理
                    extract_result = re.findall('globals.set\(\"(.*)\",.*\.responseBody(.*)\)',
                                                validate_item.replace(' ', ''))
                    if extract_result:
                        for extract_item in extract_result:
                            extract_val = 'content.responseBody' + extract_item[1].replace('[', '.').replace(
                                ']', '')
                            extract_res[extract_item[0]] = extract_val.replace('"', '')
                return variables_res, validate_res, extract_res
if __name__ == '__main__':
    #文件路径
    yaml_path='售药机.(开发测试)postman_collection.yaml'
    #将json文件转换成字典
    with open("售药机.(开发测试)postman_collection.json",'rb') as f:
        file_json =json.loads(f.read().decode('utf-8'))
    if os.path.exists(yaml_path):
        os.remove(yaml_path)
    Yaml_script = open(yaml_path, "a+", encoding='utf-8')
    cmp(file_json,Yaml_script)
    Yaml_script.close()