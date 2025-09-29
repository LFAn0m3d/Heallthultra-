import React, { useState } from 'react';
import { Alert, Button, FlatList, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { fetchTrend, TrendResponse } from '../services/api';

type MetricOption = 'bp_sys' | 'bp_dia' | 'glucose' | 'weight' | 'phq9' | 'gad7';

const metricLabels: Record<MetricOption, string> = {
  bp_sys: 'ความดันตัวบน',
  bp_dia: 'ความดันตัวล่าง',
  glucose: 'ระดับน้ำตาล',
  weight: 'น้ำหนัก',
  phq9: 'PHQ-9',
  gad7: 'GAD-7',
};

const TrendsScreen: React.FC = () => {
  const [episodeId, setEpisodeId] = useState('');
  const [metric, setMetric] = useState<MetricOption>('bp_sys');
  const [trend, setTrend] = useState<TrendResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleFetch = async () => {
    if (!episodeId) {
      Alert.alert('กรอกข้อมูลไม่ครบ', 'กรุณาระบุ episode ID');
      return;
    }
    try {
      setLoading(true);
      const response = await fetchTrend(Number(episodeId), metric);
      setTrend(response);
    } catch (err: any) {
      Alert.alert('เกิดข้อผิดพลาด', err?.message || 'ไม่สามารถดึงข้อมูลแนวโน้มได้');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.sectionTitle}>ค้นหาแนวโน้ม</Text>
      <TextInput
        style={styles.input}
        placeholder="Episode ID"
        keyboardType="numeric"
        value={episodeId}
        onChangeText={setEpisodeId}
      />
      <View style={styles.row}>
        {(Object.keys(metricLabels) as MetricOption[]).map((option) => (
          <Button
            key={option}
            title={metricLabels[option]}
            onPress={() => setMetric(option)}
            color={metric === option ? '#2563eb' : undefined}
          />
        ))}
      </View>
      <Button title={loading ? 'กำลังดึงข้อมูล...' : 'ดึงแนวโน้ม'} onPress={handleFetch} disabled={loading} />

      {trend && (
        <View style={styles.resultBox}>
          <Text style={styles.sectionTitle}>ผลลัพธ์</Text>
          <Text>แนวโน้ม: {trend.trend}</Text>
          <Text>EWMA: {trend.ewma ?? '—'}</Text>
          <Text>Slope ต่อวัน: {trend.slope_per_day ?? '—'}</Text>
          <Text>ความเชื่อมั่น: {(trend.confidence * 100).toFixed(0)}%</Text>
          <Text style={styles.pointsTitle}>จุดข้อมูล</Text>
          <FlatList
            data={trend.points}
            keyExtractor={(item, index) => `point-${index}`}
            renderItem={({ item }) => (
              <Text>{new Date(item.date).toLocaleString()} – {item.value}</Text>
            )}
            scrollEnabled={false}
          />
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    gap: 16,
    backgroundColor: '#fff',
  },
  sectionTitle: {
    fontSize: 18,
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
    flexWrap: 'wrap',
    gap: 8,
  },
  resultBox: {
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 16,
    backgroundColor: '#f9fafb',
    gap: 8,
  },
  pointsTitle: {
    marginTop: 12,
    fontWeight: '600',
  },
});

export default TrendsScreen;
