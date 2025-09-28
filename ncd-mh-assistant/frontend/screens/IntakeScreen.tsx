import React, { useState } from 'react';
import {
  Alert,
  Button,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '../app/App';
import { AnalyzePayload, analyzeCase } from '../services/api';

type IntakeNav = NativeStackNavigationProp<RootStackParamList, 'Intake'>;

type SexOption = 'M' | 'F' | 'Other';

const IntakeScreen: React.FC = () => {
  const navigation = useNavigation<IntakeNav>();
  const [age, setAge] = useState('');
  const [sex, setSex] = useState<SexOption>('M');
  const [domain, setDomain] = useState<'NCD' | 'MH'>('NCD');
  const [primarySymptom, setPrimarySymptom] = useState('');
  const [duration, setDuration] = useState('');
  const [bpSys, setBpSys] = useState('');
  const [bpDia, setBpDia] = useState('');
  const [glucose, setGlucose] = useState('');
  const [weight, setWeight] = useState('');
  const [phq9, setPhq9] = useState('');
  const [gad7, setGad7] = useState('');
  const [selfHarm, setSelfHarm] = useState(false);
  const [loading, setLoading] = useState(false);

  const parseNumber = (value: string): number | undefined => {
    if (value === '') {
      return undefined;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  };

  const handleAnalyze = async () => {
    if (!age || !primarySymptom) {
      Alert.alert('กรอกข้อมูลไม่ครบ', 'กรุณาระบุอายุและอาการหลัก');
      return;
    }

    const payload: AnalyzePayload = {
      age: Number(age),
      sex,
      domain,
      primary_symptom: primarySymptom,
      duration_days: parseNumber(duration),
      bp_sys: parseNumber(bpSys) ?? null,
      bp_dia: parseNumber(bpDia) ?? null,
      glucose: parseNumber(glucose) ?? null,
      phq9: parseNumber(phq9) ?? null,
      gad7: parseNumber(gad7) ?? null,
      weight: parseNumber(weight) ?? null,
      red_flag_answers: { self_harm: selfHarm },
    };

    try {
      setLoading(true);
      const result = await analyzeCase(payload);
      navigation.navigate('Result', { result });
    } catch (err: any) {
      Alert.alert('เกิดข้อผิดพลาด', err?.message || 'ไม่สามารถประเมินได้');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.sectionTitle}>ข้อมูลทั่วไป</Text>
      <TextInput
        style={styles.input}
        placeholder="อายุ"
        keyboardType="numeric"
        value={age}
        onChangeText={setAge}
      />
      <View style={styles.row}>
        {(['M', 'F', 'Other'] as SexOption[]).map((option) => (
          <Button
            key={option}
            title={option}
            onPress={() => setSex(option)}
            color={sex === option ? '#2563eb' : undefined}
          />
        ))}
      </View>

      <Text style={styles.sectionTitle}>สาขาอาการ</Text>
      <View style={styles.row}>
        <Button
          title="NCD"
          onPress={() => setDomain('NCD')}
          color={domain === 'NCD' ? '#2563eb' : undefined}
        />
        <Button
          title="MH"
          onPress={() => setDomain('MH')}
          color={domain === 'MH' ? '#2563eb' : undefined}
        />
      </View>

      <Text style={styles.sectionTitle}>รายละเอียดอาการ</Text>
      <TextInput
        style={styles.input}
        placeholder="อาการหลัก"
        value={primarySymptom}
        onChangeText={setPrimarySymptom}
      />
      <TextInput
        style={styles.input}
        placeholder="ระยะเวลา (วัน)"
        keyboardType="numeric"
        value={duration}
        onChangeText={setDuration}
      />

      {domain === 'NCD' && (
        <View>
          <Text style={styles.sectionTitle}>ข้อมูลโรคไม่ติดต่อ</Text>
          <TextInput
            style={styles.input}
            placeholder="ความดันตัวบน (mmHg)"
            keyboardType="numeric"
            value={bpSys}
            onChangeText={setBpSys}
          />
          <TextInput
            style={styles.input}
            placeholder="ความดันตัวล่าง (mmHg)"
            keyboardType="numeric"
            value={bpDia}
            onChangeText={setBpDia}
          />
          <TextInput
            style={styles.input}
            placeholder="ระดับน้ำตาล (mg/dL)"
            keyboardType="numeric"
            value={glucose}
            onChangeText={setGlucose}
          />
          <TextInput
            style={styles.input}
            placeholder="น้ำหนัก (kg)"
            keyboardType="numeric"
            value={weight}
            onChangeText={setWeight}
          />
        </View>
      )}

      {domain === 'MH' && (
        <View>
          <Text style={styles.sectionTitle}>ข้อมูลสุขภาพจิต</Text>
          <TextInput
            style={styles.input}
            placeholder="คะแนน PHQ-9"
            keyboardType="numeric"
            value={phq9}
            onChangeText={setPhq9}
          />
          <TextInput
            style={styles.input}
            placeholder="คะแนน GAD-7"
            keyboardType="numeric"
            value={gad7}
            onChangeText={setGad7}
          />
          <View style={styles.switchRow}>
            <Text style={styles.switchLabel}>มีความคิดทำร้ายตนเอง</Text>
            <Switch value={selfHarm} onValueChange={setSelfHarm} />
          </View>
        </View>
      )}

      <Button title={loading ? 'กำลังประมวลผล...' : 'Analyze'} onPress={handleAnalyze} disabled={loading} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: '#fff',
    gap: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
    gap: 12,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: 12,
  },
  switchLabel: {
    fontSize: 16,
  },
});

export default IntakeScreen;
