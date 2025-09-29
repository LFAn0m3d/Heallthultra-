import React from 'react';
import { Button, ScrollView, StyleSheet, Text, View } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';
import { RootStackParamList } from '../app/App';

type HomeNav = NativeStackNavigationProp<RootStackParamList, 'Home'>;

const HomeScreen: React.FC = () => {
  const navigation = useNavigation<HomeNav>();

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>NCD & Mental Health Assistant</Text>
      <Text style={styles.subtitle}>เครื่องมือช่วยประเมินเบื้องต้นสำหรับโรคไม่ติดต่อและสุขภาพจิต</Text>
      <View style={styles.warningBox}>
        <Text style={styles.warningText}>
          ผลลัพธ์นี้ไม่ใช่การวินิจฉัย หากมีอาการรุนแรงให้ไปโรงพยาบาลทันที
        </Text>
      </View>
      <View style={styles.buttonGroup}>
        <Button title="เริ่ม Intake" onPress={() => navigation.navigate('Intake')} />
      </View>
      <View style={styles.buttonGroup}>
        <Button title="ดูแนวโน้ม" onPress={() => navigation.navigate('Trends')} />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#f7f9fc',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 24,
  },
  warningBox: {
    backgroundColor: '#fff5f5',
    borderColor: '#f56565',
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    marginBottom: 32,
  },
  warningText: {
    color: '#c53030',
    textAlign: 'center',
    fontWeight: '600',
  },
  buttonGroup: {
    marginBottom: 16,
  },
});

export default HomeScreen;
